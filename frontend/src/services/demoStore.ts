import {
  Meeting,
  Transcript,
  Analysis,
  Decision,
  ActionItem,
  FollowUpPlan,
  BackendHealth,
} from '../types';
import {
  INITIAL_DEMO_MEETINGS,
  INITIAL_DEMO_TRANSCRIPTS,
  INITIAL_DEMO_ANALYSES,
  INITIAL_DEMO_DECISIONS,
  INITIAL_DEMO_ACTION_ITEMS,
  INITIAL_DEMO_FOLLOW_UPS,
} from './demoData';

const STORAGE_KEY = 'meetmind_demo_store_v1';

interface StoredData {
  meetings: Meeting[];
  transcripts: Record<string, Transcript>;
  analyses: Record<string, Analysis>;
  decisions: Decision[];
  actionItems: ActionItem[];
  followUps: FollowUpPlan[];
}

function loadInitialData(): StoredData {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      return JSON.parse(raw);
    }
  } catch (err) {
    console.warn('Failed to load demo store from localStorage:', err);
  }
  return {
    meetings: [...INITIAL_DEMO_MEETINGS],
    transcripts: { ...INITIAL_DEMO_TRANSCRIPTS },
    analyses: { ...INITIAL_DEMO_ANALYSES },
    decisions: [...INITIAL_DEMO_DECISIONS],
    actionItems: [...INITIAL_DEMO_ACTION_ITEMS],
    followUps: [...INITIAL_DEMO_FOLLOW_UPS],
  };
}

class DemoStore {
  private data: StoredData;

  constructor() {
    this.data = loadInitialData();
  }

  private save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.data));
    } catch (err) {
      console.warn('Failed to persist demo store:', err);
    }
  }

  public resetToDefault() {
    this.data = {
      meetings: [...INITIAL_DEMO_MEETINGS],
      transcripts: { ...INITIAL_DEMO_TRANSCRIPTS },
      analyses: { ...INITIAL_DEMO_ANALYSES },
      decisions: [...INITIAL_DEMO_DECISIONS],
      actionItems: [...INITIAL_DEMO_ACTION_ITEMS],
      followUps: [...INITIAL_DEMO_FOLLOW_UPS],
    };
    this.save();
  }

  // --- Meetings ---
  public getMeetings(): Meeting[] {
    return [...this.data.meetings];
  }

  public getMeeting(id: string): Meeting | undefined {
    return this.data.meetings.find((m) => m.id === id);
  }

  public createMeeting(meeting: Partial<Meeting>): Meeting {
    const id = `meet-${Date.now().toString(36)}`;
    const newMeeting: Meeting = {
      id,
      title: meeting.title || 'Untitled Meeting',
      description: meeting.description || '',
      meetingDate: meeting.meetingDate || new Date().toISOString(),
      durationSeconds: meeting.durationSeconds || 1800,
      participants: meeting.participants || [],
      meetingType: meeting.meetingType || 'Team Meeting',
      department: meeting.department || 'General',
      status: meeting.status || 'ready',
      transcriptionId: `trn-${Date.now().toString(36)}`,
      analysisStatus: meeting.analysisStatus || 'none',
      audioFilename: meeting.audioFilename || 'recorded_meeting.mp3',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.data.meetings.unshift(newMeeting);
    this.save();
    return newMeeting;
  }

  public updateMeeting(id: string, updates: Partial<Meeting>): Meeting | undefined {
    const idx = this.data.meetings.findIndex((m) => m.id === id);
    if (idx === -1) return undefined;
    this.data.meetings[idx] = {
      ...this.data.meetings[idx],
      ...updates,
      updatedAt: new Date().toISOString(),
    };
    this.save();
    return this.data.meetings[idx];
  }

  public deleteMeeting(id: string): boolean {
    const initialLen = this.data.meetings.length;
    this.data.meetings = this.data.meetings.filter((m) => m.id !== id);
    delete this.data.transcripts[id];
    delete this.data.analyses[id];
    this.data.decisions = this.data.decisions.filter((d) => d.meetingId !== id);
    this.data.actionItems = this.data.actionItems.filter((a) => a.meetingId !== id);
    this.data.followUps = this.data.followUps.filter((f) => f.meetingId !== id);
    this.save();
    return this.data.meetings.length < initialLen;
  }

  // --- Transcripts ---
  public getTranscript(meetingId: string): Transcript | undefined {
    return this.data.transcripts[meetingId];
  }

  public saveTranscript(meetingId: string, transcript: Partial<Transcript>): Transcript {
    const existing = this.data.transcripts[meetingId];
    const updated: Transcript = {
      id: existing?.id || `trn-${Date.now().toString(36)}`,
      meetingId,
      filename: transcript.filename || existing?.filename || 'audio.mp3',
      fileSizeBytes: transcript.fileSizeBytes || existing?.fileSizeBytes || 1024000,
      language: transcript.language || existing?.language || 'English (en)',
      durationSeconds: transcript.durationSeconds || existing?.durationSeconds || 1800,
      status: transcript.status || existing?.status || 'completed',
      text: transcript.text !== undefined ? transcript.text : (existing?.text || ''),
      segments: transcript.segments || existing?.segments,
      createdAt: existing?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.data.transcripts[meetingId] = updated;

    // also update meeting duration and transcriptionId
    this.updateMeeting(meetingId, {
      durationSeconds: updated.durationSeconds,
      transcriptionId: updated.id,
      status: 'ready',
    });

    this.save();
    return updated;
  }

  // --- Analyses ---
  public getAnalysis(meetingId: string): Analysis | undefined {
    return this.data.analyses[meetingId];
  }

  public saveAnalysis(meetingId: string, analysis: Partial<Analysis>): Analysis {
    const existing = this.data.analyses[meetingId];
    const updated: Analysis = {
      id: existing?.id || `ans-${Date.now().toString(36)}`,
      meetingId,
      summary: analysis.summary || existing?.summary || '',
      purpose: analysis.purpose || existing?.purpose,
      keyPoints: analysis.keyPoints || existing?.keyPoints || [],
      topics: analysis.topics || existing?.topics || [],
      risks: analysis.risks || existing?.risks || [],
      openQuestions: analysis.openQuestions || existing?.openQuestions || [],
      suggestedNextSteps: analysis.suggestedNextSteps || existing?.suggestedNextSteps || [],
      status: analysis.status || existing?.status || 'completed',
      modelUsed: analysis.modelUsed || existing?.modelUsed || 'Groq Llama-3.3-70b-versatile via LangGraph',
      createdAt: existing?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.data.analyses[meetingId] = updated;
    this.updateMeeting(meetingId, { analysisStatus: 'completed' });
    this.save();
    return updated;
  }

  // --- Decisions ---
  public getDecisions(meetingId?: string): Decision[] {
    if (meetingId) {
      return this.data.decisions.filter((d) => d.meetingId === meetingId);
    }
    return [...this.data.decisions];
  }

  public getDecision(id: string): Decision | undefined {
    return this.data.decisions.find((d) => d.id === id);
  }

  public createDecision(decision: Partial<Decision>): Decision {
    const meeting = decision.meetingId ? this.getMeeting(decision.meetingId) : undefined;
    const newDecision: Decision = {
      id: `dec-${Date.now().toString(36)}`,
      meetingId: decision.meetingId || 'general',
      meetingTitle: decision.meetingTitle || meeting?.title || 'Manual Entry',
      title: decision.title || 'Untitled Decision',
      description: decision.description || '',
      owner: decision.owner,
      status: decision.status || 'Proposed',
      category: decision.category || 'Strategy',
      evidence: decision.evidence,
      isManual: decision.isManual ?? true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.data.decisions.unshift(newDecision);
    this.save();
    return newDecision;
  }

  public updateDecision(id: string, updates: Partial<Decision>): Decision | undefined {
    const idx = this.data.decisions.findIndex((d) => d.id === id);
    if (idx === -1) return undefined;
    this.data.decisions[idx] = {
      ...this.data.decisions[idx],
      ...updates,
      updatedAt: new Date().toISOString(),
    };
    this.save();
    return this.data.decisions[idx];
  }

  public deleteDecision(id: string): boolean {
    const initialLen = this.data.decisions.length;
    this.data.decisions = this.data.decisions.filter((d) => d.id !== id);
    this.save();
    return this.data.decisions.length < initialLen;
  }

  // --- Action Items ---
  public getActionItems(meetingId?: string): ActionItem[] {
    if (meetingId) {
      return this.data.actionItems.filter((a) => a.meetingId === meetingId);
    }
    return [...this.data.actionItems];
  }

  public getActionItem(id: string): ActionItem | undefined {
    return this.data.actionItems.find((a) => a.id === id);
  }

  public createActionItem(item: Partial<ActionItem>): ActionItem {
    const meeting = item.meetingId ? this.getMeeting(item.meetingId) : undefined;
    const newItem: ActionItem = {
      id: `act-${Date.now().toString(36)}`,
      meetingId: item.meetingId || 'general',
      meetingTitle: item.meetingTitle || meeting?.title || 'Manual Entry',
      title: item.title || 'Untitled Task',
      description: item.description,
      assignee: item.assignee,
      assigneeEmail: item.assigneeEmail,
      dueDate: item.dueDate,
      priority: item.priority || 'Medium',
      status: item.status || 'To Do',
      evidence: item.evidence,
      notes: item.notes,
      isManual: item.isManual ?? true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.data.actionItems.unshift(newItem);
    this.save();
    return newItem;
  }

  public updateActionItem(id: string, updates: Partial<ActionItem>): ActionItem | undefined {
    const idx = this.data.actionItems.findIndex((a) => a.id === id);
    if (idx === -1) return undefined;
    this.data.actionItems[idx] = {
      ...this.data.actionItems[idx],
      ...updates,
      updatedAt: new Date().toISOString(),
    };
    this.save();
    return this.data.actionItems[idx];
  }

  public deleteActionItem(id: string): boolean {
    const initialLen = this.data.actionItems.length;
    this.data.actionItems = this.data.actionItems.filter((a) => a.id !== id);
    this.save();
    return this.data.actionItems.length < initialLen;
  }

  // --- Follow-up Plans ---
  public getFollowUps(meetingId?: string): FollowUpPlan[] {
    if (meetingId) {
      return this.data.followUps.filter((f) => f.meetingId === meetingId);
    }
    return [...this.data.followUps];
  }

  public getFollowUp(id: string): FollowUpPlan | undefined {
    return this.data.followUps.find((f) => f.id === id);
  }

  public getFollowUpByMeeting(meetingId: string): FollowUpPlan | undefined {
    return this.data.followUps.find((f) => f.meetingId === meetingId);
  }

  public saveFollowUp(plan: Partial<FollowUpPlan>): FollowUpPlan {
    const existing = plan.id ? this.getFollowUp(plan.id) : undefined;
    const meeting = plan.meetingId ? this.getMeeting(plan.meetingId) : undefined;

    const updated: FollowUpPlan = {
      id: existing?.id || plan.id || `flw-${Date.now().toString(36)}`,
      meetingId: plan.meetingId || existing?.meetingId || 'general',
      meetingTitle: plan.meetingTitle || meeting?.title || existing?.meetingTitle || 'Meeting Follow-up',
      title: plan.title || existing?.title || 'Execution & Follow-up Plan',
      objective: plan.objective || existing?.objective || '',
      keyOutcomes: plan.keyOutcomes || existing?.keyOutcomes || [],
      steps: plan.steps || existing?.steps || [],
      relatedActionItems: plan.relatedActionItems || existing?.relatedActionItems || [],
      risks: plan.risks || existing?.risks || [],
      checkInDates: plan.checkInDates || existing?.checkInDates || [],
      status: plan.status || existing?.status || 'Active',
      createdAt: existing?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    const idx = this.data.followUps.findIndex((f) => f.id === updated.id);
    if (idx !== -1) {
      this.data.followUps[idx] = updated;
    } else {
      this.data.followUps.unshift(updated);
    }
    this.save();
    return updated;
  }

  public deleteFollowUp(id: string): boolean {
    const initialLen = this.data.followUps.length;
    this.data.followUps = this.data.followUps.filter((f) => f.id !== id);
    this.save();
    return this.data.followUps.length < initialLen;
  }
}

export const demoStore = new DemoStore();
