export type MeetingType =
  | 'Team Meeting'
  | 'Client Meeting'
  | 'Project Review'
  | 'Planning'
  | 'Brainstorming'
  | 'Interview'
  | 'Other';

export type MeetingStatus =
  | 'queued'
  | 'uploading'
  | 'processing'
  | 'ready'
  | 'failed';

export type AnalysisStatus =
  | 'none'
  | 'pending'
  | 'completed'
  | 'failed';

export interface Meeting {
  id: string;
  title: string;
  description?: string;
  meetingDate: string; // ISO string
  durationSeconds: number;
  participants: string[];
  meetingType: MeetingType;
  department?: string;
  status: MeetingStatus;
  transcriptionId?: string;
  analysisStatus: AnalysisStatus;
  audioFilename?: string;
  createdAt: string;
  updatedAt: string;
}

export interface TranscriptSegment {
  id: string;
  start: number; // in seconds
  end: number;
  speaker?: string;
  text: string;
}

export interface Transcript {
  id: string;
  meetingId: string;
  filename: string;
  fileSizeBytes: number;
  language: string;
  durationSeconds: number;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  text: string;
  segments?: TranscriptSegment[];
  error?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Analysis {
  id: string;
  meetingId: string;
  summary: string;
  purpose?: string;
  keyPoints: string[];
  topics: string[];
  risks: string[];
  openQuestions: string[];
  suggestedNextSteps: string[];
  status: 'pending' | 'completed' | 'failed';
  modelUsed?: string;
  createdAt: string;
  updatedAt: string;
}

export type DecisionStatus = 'Proposed' | 'Confirmed' | 'Rejected' | 'Superseded';

export interface Decision {
  id: string;
  meetingId: string;
  meetingTitle?: string;
  title: string;
  description: string;
  owner?: string;
  status: DecisionStatus;
  category?: string;
  evidence?: string; // transcript quote/excerpt
  isManual?: boolean;
  createdAt: string;
  updatedAt: string;
}

export type PriorityLevel = 'Low' | 'Medium' | 'High' | 'Urgent';
export type TaskStatus = 'To Do' | 'In Progress' | 'Blocked' | 'Completed' | 'Cancelled';

export interface ActionItem {
  id: string;
  meetingId: string;
  meetingTitle?: string;
  title: string;
  description?: string;
  assignee?: string;
  assigneeEmail?: string;
  dueDate?: string;
  priority: PriorityLevel;
  status: TaskStatus;
  evidence?: string;
  notes?: string;
  isManual?: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface FollowUpStep {
  id: string;
  stepNumber: number;
  title: string;
  description?: string;
  suggestedTiming?: string;
  owner?: string;
  status: 'pending' | 'completed';
  relatedActionItemId?: string;
}

export type FollowUpStatus = 'Draft' | 'Active' | 'Completed' | 'Archived';

export interface FollowUpPlan {
  id: string;
  meetingId: string;
  meetingTitle?: string;
  title: string;
  objective: string;
  keyOutcomes?: string[];
  steps: FollowUpStep[];
  relatedActionItems?: string[];
  risks?: string[];
  checkInDates?: string[];
  status: FollowUpStatus;
  createdAt: string;
  updatedAt: string;
}

export interface BackendHealth {
  status: 'online' | 'offline' | 'degraded';
  version?: string;
  whisperAvailable?: boolean;
  groqAvailable?: boolean;
  langGraphAvailable?: boolean;
  databaseConnected?: boolean;
  lastChecked?: string;
  message?: string;
}

export interface AppNotification {
  id: string;
  title: string;
  message: string;
  timestamp: string;
  type: 'info' | 'success' | 'warning' | 'error';
  read: boolean;
  link?: string;
}
