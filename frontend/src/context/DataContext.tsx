import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import {
  Meeting,
  Transcript,
  Analysis,
  Decision,
  ActionItem,
  FollowUpPlan,
  BackendHealth,
  AppNotification,
  PriorityLevel,
  TaskStatus,
} from '../types';
import { demoStore } from '../services/demoStore';
import { healthApi } from '../services/healthApi';
import { meetingApi } from '../services/meetingApi';
import {
  transcriptionApi,
  BackendTranscriptionRecord,
} from '../services/transcriptionApi';
import { analysisApi, BackendAnalysisRecord } from '../services/analysisApi';
import { decisionApi } from '../services/decisionApi';
import {
  actionItemApi,
  BackendTaskRecord,
  BackendTaskPriority,
  BackendTaskStatus,
} from '../services/actionItemApi';
import { followUpApi, BackendFollowUpPlanResponse } from '../services/followUpApi';
import { documentApi } from '../services/documentApi';
import { workflowApi } from '../services/workflowApi';
import { toast } from 'sonner';

export type DataMode = 'demo' | 'api';

// Helper priority & status mappers between backend and frontend
const mapBackendPriority = (p?: string): PriorityLevel => {
  if (p === 'high') return 'High';
  if (p === 'low') return 'Low';
  if (p === 'urgent') return 'Urgent';
  return 'Medium';
};

const mapFrontendPriorityToBackend = (p?: PriorityLevel): BackendTaskPriority => {
  if (p === 'High' || p === 'Urgent') return 'high';
  if (p === 'Low') return 'low';
  return 'medium';
};

const mapBackendStatus = (s?: string): TaskStatus => {
  if (s === 'completed') return 'Completed';
  if (s === 'in_progress') return 'In Progress';
  if (s === 'cancelled') return 'Cancelled';
  if (s === 'blocked') return 'Blocked';
  return 'To Do';
};

const mapFrontendStatusToBackend = (s?: TaskStatus): BackendTaskStatus => {
  if (s === 'Completed') return 'completed';
  if (s === 'In Progress') return 'in_progress';
  if (s === 'Cancelled') return 'cancelled';
  return 'pending';
};

const mapBackendTaskToActionItem = (
  t: BackendTaskRecord,
  meetingTitle?: string
): ActionItem => ({
  id: t.id,
  meetingId: t.analysis_id,
  meetingTitle: meetingTitle || 'Meeting Analysis',
  title: t.description,
  description: t.description,
  assignee: t.assignee || (t.has_missing_assignee ? 'Unassigned' : 'Team Member'),
  dueDate: t.due_date || undefined,
  priority: mapBackendPriority(t.priority),
  status: mapBackendStatus(t.status),
  evidence: t.evidence_excerpt || undefined,
  createdAt: t.created_at,
  updatedAt: t.updated_at,
});

const mapBackendAnalysisToFrontend = (a: BackendAnalysisRecord): Analysis => ({
  id: a.id,
  meetingId: a.id,
  summary: a.executive_summary,
  purpose: a.meeting_purpose,
  keyPoints: a.key_discussion_points || [],
  topics: a.topics_and_themes || [],
  risks: a.risks_and_blockers || [],
  openQuestions: a.unresolved_questions || [],
  suggestedNextSteps: (a.decisions_made || []).slice(0, 3),
  status: a.status === 'completed' ? 'completed' : 'failed',
  modelUsed: a.llm_model ? `Groq Cloud (${a.llm_model})` : 'Groq LLM',
  createdAt: a.created_at,
  updatedAt: a.updated_at,
});

interface DataContextType {
  mode: DataMode;
  setMode: (mode: DataMode) => void;
  backendHealth: BackendHealth;
  checkHealth: () => Promise<void>;
  notifications: AppNotification[];
  unreadNotificationCount: number;
  addNotification: (notification: Omit<AppNotification, 'id' | 'timestamp' | 'read'>) => void;
  markNotificationRead: (id: string) => void;
  clearNotifications: () => void;

  // Meetings
  meetings: Meeting[];
  isLoadingMeetings: boolean;
  refreshMeetings: () => Promise<void>;
  getMeeting: (id: string) => Promise<Meeting | undefined>;
  createMeeting: (data: Partial<Meeting> & { text?: string }) => Promise<Meeting>;
  updateMeeting: (id: string, updates: Partial<Meeting>) => Promise<Meeting | undefined>;
  deleteMeeting: (id: string) => Promise<boolean>;

  // Transcription
  getTranscript: (meetingId: string) => Promise<Transcript | undefined>;
  saveTranscript: (meetingId: string, updates: Partial<Transcript>) => Promise<Transcript>;
  uploadAudioFile: (
    file: File,
    meetingData: Partial<Meeting>,
    language?: string,
    model?: string,
    onProgress?: (progress: number) => void,
    customText?: string
  ) => Promise<{ meeting: Meeting; transcript: Transcript }>;

  // Analysis
  getAnalysis: (meetingId: string) => Promise<Analysis | undefined>;
  triggerAnalysis: (meetingId: string) => Promise<Analysis>;

  // Decisions
  decisions: Decision[];
  refreshDecisions: (meetingId?: string) => Promise<void>;
  createDecision: (data: Partial<Decision>) => Promise<Decision>;
  updateDecision: (id: string, updates: Partial<Decision>) => Promise<Decision | undefined>;
  deleteDecision: (id: string) => Promise<boolean>;

  // Action Items
  actionItems: ActionItem[];
  refreshActionItems: (meetingId?: string) => Promise<void>;
  createActionItem: (data: Partial<ActionItem>) => Promise<ActionItem>;
  updateActionItem: (id: string, updates: Partial<ActionItem>) => Promise<ActionItem | undefined>;
  deleteActionItem: (id: string) => Promise<boolean>;

  // Follow-ups
  followUps: FollowUpPlan[];
  refreshFollowUps: (meetingId?: string) => Promise<void>;
  getFollowUpByMeeting: (meetingId: string) => Promise<FollowUpPlan | undefined>;
  saveFollowUp: (data: Partial<FollowUpPlan>) => Promise<FollowUpPlan>;
  deleteFollowUp: (id: string) => Promise<boolean>;
  generateFollowUpPlan: (meetingId: string) => Promise<FollowUpPlan>;

  // Demo store reset
  resetDemoData: () => void;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

export const DataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mode, setModeState] = useState<DataMode>(() => {
    const saved = localStorage.getItem('meetmind_data_mode') as DataMode;
    return saved === 'demo' ? 'demo' : 'api'; // Default to live API
  });

  const [backendHealth, setBackendHealth] = useState<BackendHealth>({
    status: 'offline',
  });

  const [notifications, setNotifications] = useState<AppNotification[]>([
    {
      id: 'notif-1',
      title: 'MeetMind AI Connected',
      message: 'FastAPI Backend with MongoDB Atlas, Groq LLM & LangGraph pipeline active.',
      timestamp: new Date().toISOString(),
      type: 'info',
      read: false,
    },
  ]);

  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [followUps, setFollowUps] = useState<FollowUpPlan[]>([]);
  const [isLoadingMeetings, setIsLoadingMeetings] = useState<boolean>(true);

  const setMode = (newMode: DataMode) => {
    setModeState(newMode);
    localStorage.setItem('meetmind_data_mode', newMode);
    if (newMode === 'api') {
      toast.info('Switched to Live FastAPI Backend mode');
    } else {
      toast.info('Switched to Demo / Development Mode');
    }
  };

  const checkHealth = useCallback(async () => {
    const health = await healthApi.checkHealth();
    setBackendHealth(health);
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  const addNotification = (
    notif: Omit<AppNotification, 'id' | 'timestamp' | 'read'>
  ) => {
    const newNotif: AppNotification = {
      ...notif,
      id: `notif-${Date.now()}`,
      timestamp: new Date().toISOString(),
      read: false,
    };
    setNotifications((prev) => [newNotif, ...prev.slice(0, 24)]);
  };

  const markNotificationRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const clearNotifications = () => {
    setNotifications([]);
  };

  // --- Fetch methods ---
  const refreshMeetings = useCallback(async () => {
    setIsLoadingMeetings(true);
    try {
      if (mode === 'demo') {
        const data = demoStore.getMeetings();
        setMeetings(data);
      } else {
        const data = await meetingApi.getMeetings();
        setMeetings(data);
      }
    } catch (err: any) {
      if (mode === 'api') {
        toast.error(`Backend fetch error: ${err.message}`);
        setMeetings([]);
      }
    } finally {
      setIsLoadingMeetings(false);
    }
  }, [mode]);

  const refreshDecisions = useCallback(
    async (meetingId?: string) => {
      try {
        if (mode === 'demo') {
          setDecisions(demoStore.getDecisions(meetingId));
        } else {
          const data = await decisionApi.getDecisions(meetingId);
          setDecisions(data);
        }
      } catch (err: any) {
        if (mode === 'api') {
          console.warn('Could not fetch decisions:', err.message);
        }
      }
    },
    [mode]
  );

  const refreshActionItems = useCallback(
    async (meetingId?: string) => {
      try {
        if (mode === 'demo') {
          setActionItems(demoStore.getActionItems(meetingId));
        } else {
          const res = await actionItemApi.getActionItems({
            analysis_id: meetingId,
            page_size: 100,
          });
          const mapped = res.items.map((t) => mapBackendTaskToActionItem(t));
          setActionItems(mapped);
        }
      } catch (err: any) {
        if (mode === 'api') {
          console.warn('Could not fetch action items:', err.message);
        }
      }
    },
    [mode]
  );

  const refreshFollowUps = useCallback(
    async (meetingId?: string) => {
      try {
        if (mode === 'demo') {
          setFollowUps(demoStore.getFollowUps(meetingId));
        } else {
          // If meetingId provided, load single follow up plan
          if (meetingId) {
            try {
              const planRes = await followUpApi.getFollowUpPlan(meetingId);
              const plan: FollowUpPlan = {
                id: `flw-${planRes.analysis_id}`,
                meetingId: planRes.analysis_id,
                title: 'Meeting Execution & Follow-Up Plan',
                objective:
                  planRes.ai_suggestions?.[0] ||
                  'Deliver confirmed meeting commitments and track assigned action items.',
                keyOutcomes: planRes.pending_decisions,
                steps: [
                  ...planRes.immediate_actions.map((t, idx) => ({
                    id: t.id,
                    stepNumber: idx + 1,
                    title: `[Immediate] ${t.description}`,
                    description: t.evidence_excerpt || undefined,
                    suggestedTiming: t.due_date || 'Immediate',
                    owner: t.assignee || 'Unassigned',
                    status: (t.status === 'completed' ? 'completed' : 'pending') as any,
                    relatedActionItemId: t.id,
                  })),
                  ...planRes.upcoming_tasks.map((t, idx) => ({
                    id: t.id,
                    stepNumber: planRes.immediate_actions.length + idx + 1,
                    title: t.description,
                    description: t.evidence_excerpt || undefined,
                    suggestedTiming: t.due_date || 'Scheduled',
                    owner: t.assignee || 'Unassigned',
                    status: (t.status === 'completed' ? 'completed' : 'pending') as any,
                    relatedActionItemId: t.id,
                  })),
                ],
                status: 'Active',
                createdAt: planRes.generated_at,
                updatedAt: planRes.generated_at,
              };
              setFollowUps([plan]);
            } catch {
              setFollowUps([]);
            }
          }
        }
      } catch (err: any) {
        if (mode === 'api') {
          console.warn('Could not fetch follow-ups:', err.message);
        }
      }
    },
    [mode]
  );

  useEffect(() => {
    refreshMeetings();
    refreshDecisions();
    refreshActionItems();
    refreshFollowUps();
  }, [mode, refreshMeetings, refreshDecisions, refreshActionItems, refreshFollowUps]);

  // --- Operations ---
  const getMeeting = async (id: string): Promise<Meeting | undefined> => {
    if (mode === 'demo') {
      return demoStore.getMeeting(id);
    }
    try {
      return await meetingApi.getMeeting(id);
    } catch (err: any) {
      toast.error(`Cannot find meeting: ${err.message}`);
      return undefined;
    }
  };

  const createMeeting = async (data: Partial<Meeting> & { text?: string }): Promise<Meeting> => {
    if (mode === 'demo') {
      const created = demoStore.createMeeting(data);
      refreshMeetings();
      addNotification({
        title: 'Meeting Created',
        message: `Meeting "${created.title}" recorded.`,
        type: 'success',
      });
      return created;
    }
    const created = await meetingApi.createMeeting(data);
    refreshMeetings();
    return created;
  };

  const updateMeeting = async (
    id: string,
    updates: Partial<Meeting>
  ): Promise<Meeting | undefined> => {
    if (mode === 'demo') {
      const updated = demoStore.updateMeeting(id, updates);
      refreshMeetings();
      return updated;
    }
    const updated = await meetingApi.updateMeeting(id, updates);
    refreshMeetings();
    return updated;
  };

  const deleteMeeting = async (id: string): Promise<boolean> => {
    if (mode === 'demo') {
      const ok = demoStore.deleteMeeting(id);
      refreshMeetings();
      refreshDecisions();
      refreshActionItems();
      refreshFollowUps();
      toast.success('Meeting deleted successfully');
      return ok;
    }
    await meetingApi.deleteMeeting(id);
    refreshMeetings();
    refreshDecisions();
    refreshActionItems();
    refreshFollowUps();
    toast.success('Meeting and associated records deleted from MongoDB');
    return true;
  };

  const getTranscript = async (meetingId: string): Promise<Transcript | undefined> => {
    if (mode === 'demo') {
      return demoStore.getTranscript(meetingId);
    }
    // 1. Check if meeting is in transcriptions
    try {
      const tr = await transcriptionApi.getTranscription(meetingId);
      return {
        id: tr.id,
        meetingId: tr.id,
        filename: tr.original_filename,
        fileSizeBytes: tr.file_size_bytes,
        language: tr.detected_language || tr.requested_language || 'English',
        durationSeconds: tr.audio_duration ? Math.round(tr.audio_duration) : 600,
        status: tr.status,
        text: tr.transcript_text || '',
        createdAt: tr.created_at,
        updatedAt: tr.updated_at,
      };
    } catch {
      // 2. Check if meeting is an analysis
      try {
        const analysis = await analysisApi.getAnalysis(meetingId);
        if (analysis.source_id && analysis.source_type === 'transcription') {
          const tr = await transcriptionApi.getTranscription(analysis.source_id);
          return {
            id: tr.id,
            meetingId: analysis.id,
            filename: tr.original_filename,
            fileSizeBytes: tr.file_size_bytes,
            language: tr.detected_language || 'English',
            durationSeconds: tr.audio_duration ? Math.round(tr.audio_duration) : 600,
            status: tr.status,
            text: tr.transcript_text || '',
            createdAt: tr.created_at,
            updatedAt: tr.updated_at,
          };
        } else if (analysis.source_id && (analysis.source_type === 'document' || analysis.source_type === 'pasted_text')) {
          const doc = await documentApi.getDocument(analysis.source_id);
          return {
            id: doc.id,
            meetingId: analysis.id,
            filename: doc.original_filename || 'notes.txt',
            fileSizeBytes: doc.file_size_bytes || doc.character_count,
            language: 'English',
            durationSeconds: Math.floor(doc.word_count * 0.4),
            status: doc.status,
            text: doc.text_content,
            createdAt: doc.created_at,
            updatedAt: doc.updated_at,
          };
        }
      } catch {
        // 3. Check if meeting is a document
        try {
          const doc = await documentApi.getDocument(meetingId);
          return {
            id: doc.id,
            meetingId: doc.id,
            filename: doc.original_filename || 'notes.txt',
            fileSizeBytes: doc.file_size_bytes || doc.character_count,
            language: 'English',
            durationSeconds: Math.floor(doc.word_count * 0.4),
            status: doc.status,
            text: doc.text_content,
            createdAt: doc.created_at,
            updatedAt: doc.updated_at,
          };
        } catch {
          return undefined;
        }
      }
    }
    return undefined;
  };

  const saveTranscript = async (
    meetingId: string,
    updates: Partial<Transcript>
  ): Promise<Transcript> => {
    if (mode === 'demo') {
      const saved = demoStore.saveTranscript(meetingId, updates);
      toast.success('Transcript changes saved');
      refreshMeetings();
      return saved;
    }

    if (updates.text) {
      try {
        await transcriptionApi.updateTranscription(meetingId, updates.text);
      } catch {
        // If not in transcriptions collection directly, check if it's an analysis
        try {
          const analysis = await analysisApi.getAnalysis(meetingId);
          if (analysis.source_id && analysis.source_type === 'transcription') {
            await transcriptionApi.updateTranscription(analysis.source_id, updates.text);
          }
        } catch {
          console.debug('Transcript updated for document:', meetingId);
        }
      }
    }

    toast.success('Transcript updated');
    refreshMeetings();
    const updated = await getTranscript(meetingId);
    if (!updated) {
      return {
        id: meetingId,
        meetingId,
        filename: 'notes.txt',
        fileSizeBytes: updates.text?.length || 0,
        language: 'English',
        durationSeconds: 300,
        status: 'completed',
        text: updates.text || '',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
    }
    return updated;
  };

  const uploadAudioFile = async (
    file: File,
    meetingData: Partial<Meeting>,
    language = 'auto',
    model = 'whisper-medium',
    onProgress?: (progress: number) => void,
    customText?: string
  ): Promise<{ meeting: Meeting; transcript: Transcript }> => {
    if (mode === 'demo') {
      if (onProgress) {
        onProgress(30);
        await new Promise((r) => setTimeout(r, 200));
        onProgress(70);
        await new Promise((r) => setTimeout(r, 200));
        onProgress(100);
      }

      const createdMeeting = demoStore.createMeeting({
        ...meetingData,
        title: meetingData.title || file.name.replace(/\.[^/.]+$/, ''),
        audioFilename: file.name,
        durationSeconds: Math.floor(file.size / 32000) || 1200,
        status: 'ready',
        analysisStatus: 'none',
      });

      const transcriptText =
        customText ||
        `Host: Welcome everyone to "${createdMeeting.title}". Today's agenda covers milestones, deliverables, and resource allocation.
Participant A: Metrics look solid across the board. We are tracking on schedule for the upcoming deployment.
Participant B: Confirmed. Let's document all follow-ups and assign owners.`;

      const savedTranscript = demoStore.saveTranscript(createdMeeting.id, {
        filename: file.name,
        fileSizeBytes: file.size,
        language: language === 'auto' ? 'English (Auto-detected)' : language,
        durationSeconds: createdMeeting.durationSeconds,
        status: 'completed',
        text: transcriptText,
      });

      refreshMeetings();
      return { meeting: createdMeeting, transcript: savedTranscript };
    }

    // Live API mode:
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    const isDocument = ext === '.pdf' || ext === '.docx' || ext === '.doc' || ext === '.txt';

    if (isDocument) {
      if (onProgress) onProgress(40);
      const doc = await documentApi.uploadDocument(file, meetingData.title);
      if (onProgress) onProgress(100);

      const createdMeeting: Meeting = {
        id: doc.id,
        title: meetingData.title || doc.title || file.name,
        description: meetingData.description || doc.text_content.slice(0, 150),
        meetingDate: meetingData.meetingDate || doc.created_at,
        durationSeconds: Math.max(300, Math.floor(doc.word_count * 0.4)),
        participants: meetingData.participants || ['Attendees'],
        meetingType: meetingData.meetingType || 'Planning',
        department: meetingData.department || 'Documents',
        status: 'ready',
        analysisStatus: 'none',
        createdAt: doc.created_at,
        updatedAt: doc.updated_at,
      };

      const transcript: Transcript = {
        id: doc.id,
        meetingId: doc.id,
        filename: file.name,
        fileSizeBytes: file.size,
        language: 'English',
        durationSeconds: createdMeeting.durationSeconds,
        status: 'completed',
        text: doc.text_content,
        createdAt: doc.created_at,
        updatedAt: doc.updated_at,
      };

      refreshMeetings();
      return { meeting: createdMeeting, transcript };
    }

    // Audio file upload to Whisper
    const uploadRes = await transcriptionApi.uploadAudio({
      file,
      language: language !== 'auto' ? language : undefined,
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded * 50) / e.total)); // 0 - 50%
        }
      },
    });

    if (onProgress) onProgress(60);

    // Poll until Whisper transcription completes
    const completedTr = await transcriptionApi.pollTranscription(
      uploadRes.job_id,
      (status) => {
        if (onProgress) {
          if (status === 'processing') onProgress(75);
          if (status === 'completed') onProgress(100);
        }
      }
    );

    const createdMeeting: Meeting = {
      id: completedTr.id,
      title: meetingData.title || file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' '),
      description: meetingData.description || `Audio recording (${completedTr.file_format.toUpperCase()})`,
      meetingDate: meetingData.meetingDate || completedTr.created_at,
      durationSeconds: completedTr.audio_duration ? Math.round(completedTr.audio_duration) : 600,
      participants: meetingData.participants || ['Speakers'],
      meetingType: meetingData.meetingType || 'Project Review',
      department: meetingData.department || 'Engineering',
      status: 'ready',
      transcriptionId: completedTr.id,
      analysisStatus: 'none',
      audioFilename: completedTr.original_filename,
      createdAt: completedTr.created_at,
      updatedAt: completedTr.updated_at,
    };

    const transcript: Transcript = {
      id: completedTr.id,
      meetingId: completedTr.id,
      filename: completedTr.original_filename,
      fileSizeBytes: completedTr.file_size_bytes,
      language: completedTr.detected_language || 'English',
      durationSeconds: createdMeeting.durationSeconds,
      status: completedTr.status,
      text: completedTr.transcript_text || '',
      createdAt: completedTr.created_at,
      updatedAt: completedTr.updated_at,
    };

    refreshMeetings();
    return { meeting: createdMeeting, transcript };
  };

  const getAnalysis = async (meetingId: string): Promise<Analysis | undefined> => {
    if (mode === 'demo') {
      return demoStore.getAnalysis(meetingId);
    }
    try {
      const backendAnalysis = await analysisApi.getAnalysis(meetingId);
      return mapBackendAnalysisToFrontend(backendAnalysis);
    } catch {
      return undefined;
    }
  };

  const triggerAnalysis = async (meetingId: string): Promise<Analysis> => {
    if (mode === 'demo') {
      await new Promise((r) => setTimeout(r, 700));
      const meeting = demoStore.getMeeting(meetingId);

      const generatedAnalysis: Analysis = {
        id: `ans-${Date.now().toString(36)}`,
        meetingId,
        summary: `The session addressed strategic priorities for "${meeting?.title || 'the project'}". Deliverables and milestones were agreed upon with cross-functional accountability.`,
        purpose: 'Strategic coordination and execution planning.',
        keyPoints: [
          'Reviewed project metrics and baseline allocations.',
          'Consensus reached on target deadlines and operational handoffs.',
          'Identified proactive risk mitigation steps.',
        ],
        topics: ['Operations', 'Roadmap', 'Quality Assurance'],
        risks: ['Tight delivery windows for downstream validation.'],
        openQuestions: ['Are all team members briefed on the updated workflow?'],
        suggestedNextSteps: ['Distribute recap notes to stakeholders.'],
        status: 'completed',
        modelUsed: 'Groq Cloud LLM via LangGraph',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      demoStore.saveAnalysis(meetingId, generatedAnalysis);
      refreshMeetings();
      refreshDecisions();
      refreshActionItems();
      return generatedAnalysis;
    }

    // Live API mode: Run end-to-end LangGraph pipeline or Analysis + Tasks extraction
    let sourceType: 'transcription' | 'document' | 'direct_text' | 'pasted_text' = 'document';
    let sourceId: string | null = meetingId;
    let title: string | undefined = undefined;
    let directText: string | undefined = undefined;

    // 1. Try finding in transcriptions
    try {
      const tr = await transcriptionApi.getTranscription(meetingId);
      sourceType = 'transcription';
      sourceId = tr.id;
      title = tr.original_filename?.replace(/\.[^/.]+$/, '');
    } catch {
      // 2. Try finding in documents
      try {
        const doc = await documentApi.getDocument(meetingId);
        sourceType = doc.source_type === 'pasted_text' ? 'pasted_text' : 'document';
        sourceId = doc.id;
        title = doc.title || doc.original_filename || 'Meeting Document';
      } catch {
        // 3. Try finding in analyses
        try {
          const existingAnalysis = await analysisApi.getAnalysis(meetingId);
          if (existingAnalysis.source_id) {
            sourceType = existingAnalysis.source_type === 'transcription' ? 'transcription' : 'document';
            sourceId = existingAnalysis.source_id;
            title = existingAnalysis.title || 'Meeting Analysis';
          } else {
            sourceType = 'direct_text';
            sourceId = null;
            directText = existingAnalysis.executive_summary;
            title = existingAnalysis.title || 'Meeting Analysis';
          }
        } catch {
          // If not found, use direct text
          sourceType = 'direct_text';
          sourceId = null;
          directText = 'Executive meeting session.';
        }
      }
    }

    // Execute synchronous workflow or analysis creation
    const workflowRes = await workflowApi.runSyncWorkflow({
      source_type: sourceType,
      source_id: sourceId,
      text: directText,
      title: title || 'Executive Meeting Analysis',
      force_reanalyze: true,
    });

    if (workflowRes.analysis) {
      const frontendAnalysis = mapBackendAnalysisToFrontend(workflowRes.analysis);
      refreshMeetings();
      refreshDecisions();
      refreshActionItems();
      refreshFollowUps(workflowRes.analysis.id);

      addNotification({
        title: 'AI Analysis Complete',
        message: `Intelligence extracted with ${workflowRes.tasks?.length || 0} action items.`,
        type: 'success',
      });

      return frontendAnalysis;
    }

    // Fallback: direct analysis creation
    const directAnalysis = await analysisApi.createAnalysis({
      source_type: sourceType === 'pasted_text' ? 'document' : (sourceType as any),
      source_id: sourceId || undefined,
      text: directText,
      title: title || 'Executive Meeting Analysis',
    });

    await actionItemApi.extractActionItems(directAnalysis.id, true);
    const mapped = mapBackendAnalysisToFrontend(directAnalysis);
    refreshMeetings();
    refreshDecisions();
    refreshActionItems();
    refreshFollowUps(directAnalysis.id);
    return mapped;
  };

  // Decisions operations
  const createDecision = async (data: Partial<Decision>): Promise<Decision> => {
    if (mode === 'demo') {
      const created = demoStore.createDecision(data);
      refreshDecisions();
      toast.success('Decision recorded');
      return created;
    }
    const created = await decisionApi.createDecision(data);
    setDecisions((prev) => [created, ...prev]);
    toast.success('Decision recorded');
    return created;
  };

  const updateDecision = async (
    id: string,
    updates: Partial<Decision>
  ): Promise<Decision | undefined> => {
    if (mode === 'demo') {
      const updated = demoStore.updateDecision(id, updates);
      refreshDecisions();
      toast.success('Decision updated');
      return updated;
    }
    const updated = await decisionApi.updateDecision(id, updates);
    setDecisions((prev) => prev.map((d) => (d.id === id ? updated : d)));
    toast.success('Decision updated');
    return updated;
  };

  const deleteDecision = async (id: string): Promise<boolean> => {
    if (mode === 'demo') {
      const ok = demoStore.deleteDecision(id);
      refreshDecisions();
      toast.success('Decision removed');
      return ok;
    }
    await decisionApi.deleteDecision(id);
    setDecisions((prev) => prev.filter((d) => d.id !== id));
    toast.success('Decision removed');
    return true;
  };

  // Action items operations
  const createActionItem = async (data: Partial<ActionItem>): Promise<ActionItem> => {
    if (mode === 'demo') {
      const created = demoStore.createActionItem(data);
      refreshActionItems();
      toast.success('Action item created');
      return created;
    }
    const created = await actionItemApi.createActionItem({
      analysis_id: data.meetingId || meetings[0]?.id || 'global_task',
      description: data.title || data.description || 'New action item',
      assignee: data.assignee && data.assignee !== 'Unassigned' ? data.assignee : undefined,
      due_date: data.dueDate,
      priority: mapFrontendPriorityToBackend(data.priority),
      status: mapFrontendStatusToBackend(data.status),
      evidence_excerpt: data.evidence,
    });
    const mapped = mapBackendTaskToActionItem(created, data.meetingTitle);
    setActionItems((prev) => [mapped, ...prev]);
    toast.success('Action item created');
    return mapped;
  };

  const updateActionItem = async (
    id: string,
    updates: Partial<ActionItem>
  ): Promise<ActionItem | undefined> => {
    if (mode === 'demo') {
      const updated = demoStore.updateActionItem(id, updates);
      refreshActionItems();
      toast.success('Task updated');
      return updated;
    }
    const updated = await actionItemApi.updateActionItem(id, {
      description: updates.title || updates.description,
      assignee: updates.assignee,
      due_date: updates.dueDate,
      priority: mapFrontendPriorityToBackend(updates.priority),
      status: mapFrontendStatusToBackend(updates.status),
      evidence_excerpt: updates.evidence,
    });
    const mapped = mapBackendTaskToActionItem(updated, updates.meetingTitle);
    setActionItems((prev) => prev.map((t) => (t.id === id ? mapped : t)));
    toast.success('Task updated');
    return mapped;
  };

  const deleteActionItem = async (id: string): Promise<boolean> => {
    if (mode === 'demo') {
      const ok = demoStore.deleteActionItem(id);
      refreshActionItems();
      toast.success('Task deleted');
      return ok;
    }
    await actionItemApi.deleteActionItem(id);
    setActionItems((prev) => prev.filter((t) => t.id !== id));
    toast.success('Task deleted from backend');
    return true;
  };

  // Follow-up operations
  const getFollowUpByMeeting = async (
    meetingId: string
  ): Promise<FollowUpPlan | undefined> => {
    if (mode === 'demo') {
      return demoStore.getFollowUpByMeeting(meetingId);
    }
    try {
      const planRes = await followUpApi.getFollowUpPlan(meetingId);
      return {
        id: `flw-${planRes.analysis_id}`,
        meetingId: planRes.analysis_id,
        title: 'Meeting Execution & Follow-Up Plan',
        objective:
          planRes.ai_suggestions?.[0] ||
          'Fulfill all assigned meeting action items and commitments.',
        keyOutcomes: planRes.pending_decisions,
        steps: [
          ...planRes.immediate_actions.map((t, idx) => ({
            id: t.id,
            stepNumber: idx + 1,
            title: `[Immediate] ${t.description}`,
            description: t.evidence_excerpt || undefined,
            suggestedTiming: t.due_date || 'Immediate',
            owner: t.assignee || 'Unassigned',
            status: (t.status === 'completed' ? 'completed' : 'pending') as any,
            relatedActionItemId: t.id,
          })),
          ...planRes.upcoming_tasks.map((t, idx) => ({
            id: t.id,
            stepNumber: planRes.immediate_actions.length + idx + 1,
            title: t.description,
            description: t.evidence_excerpt || undefined,
            suggestedTiming: t.due_date || 'Scheduled',
            owner: t.assignee || 'Unassigned',
            status: (t.status === 'completed' ? 'completed' : 'pending') as any,
            relatedActionItemId: t.id,
          })),
        ],
        status: 'Active',
        createdAt: planRes.generated_at,
        updatedAt: planRes.generated_at,
      };
    } catch {
      return undefined;
    }
  };

  const saveFollowUp = async (data: Partial<FollowUpPlan>): Promise<FollowUpPlan> => {
    if (mode === 'demo') {
      const saved = demoStore.saveFollowUp(data);
      refreshFollowUps();
      toast.success('Follow-up plan saved');
      return saved;
    }
    toast.success('Follow-up plan synchronized');
    return data as FollowUpPlan;
  };

  const deleteFollowUp = async (id: string): Promise<boolean> => {
    if (mode === 'demo') {
      const ok = demoStore.deleteFollowUp(id);
      refreshFollowUps();
      toast.success('Follow-up plan deleted');
      return ok;
    }
    setFollowUps((prev) => prev.filter((f) => f.id !== id));
    toast.success('Follow-up plan removed');
    return true;
  };

  const generateFollowUpPlan = async (meetingId: string): Promise<FollowUpPlan> => {
    if (mode === 'demo') {
      await new Promise((r) => setTimeout(r, 600));
      const meeting = demoStore.getMeeting(meetingId);
      const actions = demoStore.getActionItems(meetingId);

      const generatedPlan: FollowUpPlan = {
        id: `flw-${Date.now().toString(36)}`,
        meetingId,
        meetingTitle: meeting?.title,
        title: `${meeting?.title || 'Meeting'} Execution & Milestone Plan`,
        objective: `Deliver confirmed outcomes and fulfill all assigned action items.`,
        keyOutcomes: ['Complete all action items within target milestones'],
        steps: actions.map((act, i) => ({
          id: `step-${i + 1}`,
          stepNumber: i + 1,
          title: act.title,
          description: act.description,
          suggestedTiming: act.dueDate || 'Within 5 business days',
          owner: act.assignee || 'Unassigned',
          status: 'pending' as const,
          relatedActionItemId: act.id,
        })),
        status: 'Active',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      demoStore.saveFollowUp(generatedPlan);
      refreshFollowUps();
      toast.success('Follow-up plan generated');
      return generatedPlan;
    }

    const plan = await getFollowUpByMeeting(meetingId);
    if (!plan) throw new Error('Could not generate follow-up plan from backend');
    refreshFollowUps(meetingId);
    return plan;
  };

  const resetDemoData = () => {
    demoStore.resetToDefault();
    refreshMeetings();
    refreshDecisions();
    refreshActionItems();
    refreshFollowUps();
    toast.success('Demo data reset');
  };

  const unreadNotificationCount = notifications.filter((n) => !n.read).length;

  return (
    <DataContext.Provider
      value={{
        mode,
        setMode,
        backendHealth,
        checkHealth,
        notifications,
        unreadNotificationCount,
        addNotification,
        markNotificationRead,
        clearNotifications,

        meetings,
        isLoadingMeetings,
        refreshMeetings,
        getMeeting,
        createMeeting,
        updateMeeting,
        deleteMeeting,

        getTranscript,
        saveTranscript,
        uploadAudioFile,

        getAnalysis,
        triggerAnalysis,

        decisions,
        refreshDecisions,
        createDecision,
        updateDecision,
        deleteDecision,

        actionItems,
        refreshActionItems,
        createActionItem,
        updateActionItem,
        deleteActionItem,

        followUps,
        refreshFollowUps,
        getFollowUpByMeeting,
        saveFollowUp,
        deleteFollowUp,
        generateFollowUpPlan,

        resetDemoData,
      }}
    >
      {children}
    </DataContext.Provider>
  );
};

export const useData = () => {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
};
