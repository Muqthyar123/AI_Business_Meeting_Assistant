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
} from '../types';
import { demoStore } from '../services/demoStore';
import { healthApi } from '../services/healthApi';
import { meetingApi } from '../services/meetingApi';
import { transcriptionApi } from '../services/transcriptionApi';
import { analysisApi } from '../services/analysisApi';
import { decisionApi } from '../services/decisionApi';
import { actionItemApi } from '../services/actionItemApi';
import { followUpApi } from '../services/followUpApi';
import { toast } from 'sonner';

export type DataMode = 'demo' | 'api';

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
  createMeeting: (data: Partial<Meeting>) => Promise<Meeting>;
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
    return saved === 'api' ? 'api' : 'demo';
  });

  const [backendHealth, setBackendHealth] = useState<BackendHealth>({
    status: 'offline',
  });

  const [notifications, setNotifications] = useState<AppNotification[]>([
    {
      id: 'notif-1',
      title: 'Welcome to MeetMind',
      message: 'Demo mode loaded with sample executive meetings, transcripts, and action items.',
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
        toast.error(`Failed to fetch meetings from backend: ${err.message}`);
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
          toast.error(`Failed to fetch decisions: ${err.message}`);
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
          const data = await actionItemApi.getActionItems(meetingId);
          setActionItems(data);
        }
      } catch (err: any) {
        if (mode === 'api') {
          toast.error(`Failed to fetch action items: ${err.message}`);
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
          const data = await followUpApi.getFollowUps(meetingId);
          setFollowUps(data);
        }
      } catch (err: any) {
        if (mode === 'api') {
          toast.error(`Failed to fetch follow-ups: ${err.message}`);
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

  const createMeeting = async (data: Partial<Meeting>): Promise<Meeting> => {
    if (mode === 'demo') {
      const created = demoStore.createMeeting(data);
      refreshMeetings();
      addNotification({
        title: 'Meeting Created',
        message: `Meeting "${created.title}" successfully recorded.`,
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
    toast.success('Meeting deleted from database');
    return true;
  };

  const getTranscript = async (meetingId: string): Promise<Transcript | undefined> => {
    if (mode === 'demo') {
      return demoStore.getTranscript(meetingId);
    }
    const meeting = await getMeeting(meetingId);
    if (!meeting?.transcriptionId) return undefined;
    try {
      return await transcriptionApi.getTranscription(meeting.transcriptionId);
    } catch {
      return undefined;
    }
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
    const existing = await getTranscript(meetingId);
    if (!existing) throw new Error('No transcript to update');
    const saved = await transcriptionApi.updateTranscription(existing.id, updates);
    toast.success('Transcript saved to backend');
    refreshMeetings();
    return saved;
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
      // Simulate stepped upload progress
      if (onProgress) {
        onProgress(30);
        await new Promise((r) => setTimeout(r, 200));
        onProgress(70);
        await new Promise((r) => setTimeout(r, 200));
        onProgress(100);
      }

      // Create new meeting
      const createdMeeting = demoStore.createMeeting({
        ...meetingData,
        title: meetingData.title || file.name.replace(/\.[^/.]+$/, ''),
        audioFilename: file.name,
        durationSeconds: Math.floor(file.size / 32000) || 1200,
        status: 'ready',
        analysisStatus: 'none',
      });

      // Use customText if provided (from manual transcript or doc extraction), else fallback to sample text
      const transcriptText =
        customText ||
        `Host: Welcome everyone to "${createdMeeting.title}". Today's agenda covers project milestones, resource allocation, and key deliverables.

Participant A: Thanks for organizing. We have reviewed the initial metrics and everything is progressing according to schedule.

Participant B: I agree. Let's make sure we document all follow-ups and assign owners before we adjourn.

Host: Sounds good. We'll finalize the decisions and distribute the action items by end of week.`;

      const savedTranscript = demoStore.saveTranscript(createdMeeting.id, {
        filename: file.name,
        fileSizeBytes: file.size,
        language: language === 'auto' ? 'English (Auto-detected)' : language,
        durationSeconds: createdMeeting.durationSeconds,
        status: 'completed',
        text: transcriptText,
      });

      addNotification({
        title: 'Transcription Ready',
        message: `Audio file "${file.name}" was transcribed into text.`,
        type: 'success',
      });

      refreshMeetings();
      return { meeting: createdMeeting, transcript: savedTranscript };
    }

    // In Live API mode:
    const newMeeting = await meetingApi.createMeeting(meetingData);
    const transcript = await transcriptionApi.uploadAudio({
      file,
      meetingId: newMeeting.id,
      language,
      model,
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded * 100) / e.total));
        }
      },
    });

    refreshMeetings();
    return { meeting: newMeeting, transcript };
  };

  const getAnalysis = async (meetingId: string): Promise<Analysis | undefined> => {
    if (mode === 'demo') {
      return demoStore.getAnalysis(meetingId);
    }
    try {
      return await analysisApi.getMeetingAnalysis(meetingId);
    } catch {
      return undefined;
    }
  };

  const triggerAnalysis = async (meetingId: string): Promise<Analysis> => {
    if (mode === 'demo') {
      await new Promise((r) => setTimeout(r, 900)); // subtle realistic processing delay
      const meeting = demoStore.getMeeting(meetingId);
      const transcript = demoStore.getTranscript(meetingId);

      const generatedAnalysis: Analysis = {
        id: `ans-${Date.now().toString(36)}`,
        meetingId,
        summary: `The session addressed key strategic objectives for "${meeting?.title || 'the project'}". Key operational milestones and immediate deliverables were agreed upon with clear cross-functional accountability.`,
        purpose: 'Strategy alignment and tactical milestone coordination.',
        keyPoints: [
          'Detailed review of project metrics and baseline resource allocation.',
          'Consensus reached on target deadlines and operational handoffs.',
          'Identified proactive risk management steps for upcoming sprint cycles.',
        ],
        topics: ['Operations', 'Roadmap', 'Quality Assurance', 'Resource Allocation'],
        risks: ['Tight timeline for downstream client validation handoff.'],
        openQuestions: ['Are all team members briefed on the updated workflow?'],
        suggestedNextSteps: [
          'Distribute recap notes to stakeholders.',
          'Schedule sprint check-in next week.',
        ],
        status: 'completed',
        modelUsed: 'Groq Llama-3.3-70b-versatile via LangGraph',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      demoStore.saveAnalysis(meetingId, generatedAnalysis);

      // Also generate initial decision & action item if none exist
      if (demoStore.getDecisions(meetingId).length === 0) {
        demoStore.createDecision({
          meetingId,
          meetingTitle: meeting?.title,
          title: 'Adopt updated operational delivery milestones',
          description: 'Team agreed to proceed with proposed roadmap targets and deliverable sequence.',
          owner: meeting?.participants[0] || 'Team Lead',
          status: 'Confirmed',
          category: 'Operations',
          evidence: 'Transcript excerpt: "Sounds good. We\'ll finalize the decisions and distribute the action items by end of week."',
        });
      }

      if (demoStore.getActionItems(meetingId).length === 0) {
        demoStore.createActionItem({
          meetingId,
          meetingTitle: meeting?.title,
          title: 'Distribute meeting decisions and action items',
          description: 'Send finalized summary and next steps to all attendees.',
          assignee: meeting?.participants[0] || 'Meeting Host',
          dueDate: new Date(Date.now() + 86400000 * 3).toISOString(),
          priority: 'High',
          status: 'To Do',
          evidence: 'Transcript excerpt: "Sounds good. We\'ll finalize the decisions and distribute the action items by end of week."',
        });
      }

      addNotification({
        title: 'AI Analysis Complete',
        message: `Generated insights, decisions, and action items for "${meeting?.title}".`,
        type: 'success',
      });

      refreshMeetings();
      refreshDecisions();
      refreshActionItems();
      return generatedAnalysis;
    }

    // In API mode:
    const result = await analysisApi.analyzeMeeting(meetingId);
    refreshMeetings();
    refreshDecisions();
    refreshActionItems();
    return result;
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
    refreshDecisions();
    toast.success('Decision saved');
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
    refreshDecisions();
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
    refreshDecisions();
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
    const created = await actionItemApi.createActionItem(data);
    refreshActionItems();
    toast.success('Action item created');
    return created;
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
    const updated = await actionItemApi.updateActionItem(id, updates);
    refreshActionItems();
    toast.success('Task updated');
    return updated;
  };

  const deleteActionItem = async (id: string): Promise<boolean> => {
    if (mode === 'demo') {
      const ok = demoStore.deleteActionItem(id);
      refreshActionItems();
      toast.success('Task deleted');
      return ok;
    }
    await actionItemApi.deleteActionItem(id);
    refreshActionItems();
    toast.success('Task deleted');
    return true;
  };

  // Follow-up operations
  const getFollowUpByMeeting = async (
    meetingId: string
  ): Promise<FollowUpPlan | undefined> => {
    if (mode === 'demo') {
      return demoStore.getFollowUpByMeeting(meetingId);
    }
    const plans = await followUpApi.getFollowUps(meetingId);
    return plans[0];
  };

  const saveFollowUp = async (data: Partial<FollowUpPlan>): Promise<FollowUpPlan> => {
    if (mode === 'demo') {
      const saved = demoStore.saveFollowUp(data);
      refreshFollowUps();
      toast.success('Follow-up plan saved');
      return saved;
    }
    const saved = data.id
      ? await followUpApi.updateFollowUp(data.id, data)
      : await followUpApi.generateFollowUp(data.meetingId!);
    refreshFollowUps();
    toast.success('Follow-up plan saved');
    return saved;
  };

  const deleteFollowUp = async (id: string): Promise<boolean> => {
    if (mode === 'demo') {
      const ok = demoStore.deleteFollowUp(id);
      refreshFollowUps();
      toast.success('Follow-up plan deleted');
      return ok;
    }
    await followUpApi.deleteFollowUp(id);
    refreshFollowUps();
    toast.success('Follow-up plan deleted');
    return true;
  };

  const generateFollowUpPlan = async (meetingId: string): Promise<FollowUpPlan> => {
    if (mode === 'demo') {
      await new Promise((r) => setTimeout(r, 700));
      const meeting = demoStore.getMeeting(meetingId);
      const actions = demoStore.getActionItems(meetingId);
      const decisionsList = demoStore.getDecisions(meetingId);

      const generatedPlan: FollowUpPlan = {
        id: `flw-${Date.now().toString(36)}`,
        meetingId,
        meetingTitle: meeting?.title,
        title: `${meeting?.title || 'Meeting'} Execution & Milestone Plan`,
        objective: `Deliver confirmed outcomes and fulfill all assigned action items from the ${meeting?.title || 'session'}.`,
        keyOutcomes: [
          `Execute on ${decisionsList.length || 1} confirmed decisions without timeline slippage`,
          `Complete all ${actions.length || 2} priority action items within target milestones`,
          'Provide transparent progress check-in reporting to stakeholders',
        ],
        steps: actions.map((act, i) => ({
          id: `step-${i + 1}`,
          stepNumber: i + 1,
          title: act.title,
          description: act.description,
          suggestedTiming: act.dueDate ? `Due ${new Date(act.dueDate).toLocaleDateString()}` : 'Within 5 business days',
          owner: act.assignee || 'Unassigned',
          status: 'pending' as const,
          relatedActionItemId: act.id,
        })),
        checkInDates: [
          new Date(Date.now() + 86400000 * 3).toISOString().split('T')[0],
          new Date(Date.now() + 86400000 * 7).toISOString().split('T')[0],
        ],
        status: 'Active',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      demoStore.saveFollowUp(generatedPlan);
      refreshFollowUps();
      toast.success('Follow-up plan generated with LangGraph');
      return generatedPlan;
    }

    const plan = await followUpApi.generateFollowUp(meetingId);
    refreshFollowUps();
    return plan;
  };

  const resetDemoData = () => {
    demoStore.resetToDefault();
    refreshMeetings();
    refreshDecisions();
    refreshActionItems();
    refreshFollowUps();
    toast.success('Demo data reset to default executive dataset');
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
