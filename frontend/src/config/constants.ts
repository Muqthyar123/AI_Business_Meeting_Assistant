import { MeetingType, PriorityLevel, TaskStatus, DecisionStatus } from '../types';

export const SUPPORTED_AUDIO_FORMATS = [
  'audio/mpeg',
  'audio/mp3',
  'audio/wav',
  'audio/x-wav',
  'audio/m4a',
  'audio/x-m4a',
  'audio/flac',
  'audio/x-flac',
  'audio/ogg',
  'audio/webm',
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
];

export const SUPPORTED_EXTENSIONS = [
  '.pdf',
  '.docx',
  '.doc',
  '.txt',
  '.mp3',
  '.wav',
  '.m4a',
  '.flac',
  '.ogg',
  '.webm',
];

export const MAX_FILE_SIZE_BYTES = 250 * 1024 * 1024; // 250 MB
export const MAX_FILE_SIZE_LABEL = '250 MB';

export const MEETING_TYPES: MeetingType[] = [
  'Team Meeting',
  'Client Meeting',
  'Project Review',
  'Planning',
  'Brainstorming',
  'Interview',
  'Other',
];

export const TRANSCRIPTION_LANGUAGES = [
  { code: 'auto', label: 'Auto Detect (Recommended)' },
  { code: 'en', label: 'English' },
  { code: 'es', label: 'Spanish' },
  { code: 'fr', label: 'French' },
  { code: 'de', label: 'German' },
  { code: 'it', label: 'Italian' },
  { code: 'pt', label: 'Portuguese' },
  { code: 'zh', label: 'Chinese' },
  { code: 'ja', label: 'Japanese' },
  { code: 'ko', label: 'Korean' },
  { code: 'hi', label: 'Hindi' },
];

export const WHISPER_MODELS = [
  { id: 'whisper-base', label: 'Whisper Base (Fastest, low latency)' },
  { id: 'whisper-small', label: 'Whisper Small (Balanced speed & accuracy)' },
  { id: 'whisper-medium', label: 'Whisper Medium (High accuracy, recommended)' },
  { id: 'whisper-large-v3', label: 'Whisper Large v3 (Maximum precision)' },
];

export const PRIORITY_CONFIG: Record<
  PriorityLevel,
  { label: string; bg: string; text: string; border: string }
> = {
  Urgent: {
    label: 'Urgent',
    bg: 'bg-red-50 dark:bg-red-950/40',
    text: 'text-red-700 dark:text-red-400',
    border: 'border-red-200 dark:border-red-800/60',
  },
  High: {
    label: 'High',
    bg: 'bg-amber-50 dark:bg-amber-950/40',
    text: 'text-amber-700 dark:text-amber-400',
    border: 'border-amber-200 dark:border-amber-800/60',
  },
  Medium: {
    label: 'Medium',
    bg: 'bg-blue-50 dark:bg-blue-950/40',
    text: 'text-blue-700 dark:text-blue-400',
    border: 'border-blue-200 dark:border-blue-800/60',
  },
  Low: {
    label: 'Low',
    bg: 'bg-slate-50 dark:bg-slate-800/60',
    text: 'text-slate-700 dark:text-slate-300',
    border: 'border-slate-200 dark:border-slate-700',
  },
};

export const TASK_STATUS_CONFIG: Record<
  TaskStatus,
  { label: string; bg: string; text: string; dot: string }
> = {
  'To Do': {
    label: 'To Do',
    bg: 'bg-slate-100 dark:bg-slate-800',
    text: 'text-slate-700 dark:text-slate-300',
    dot: 'bg-slate-400',
  },
  'In Progress': {
    label: 'In Progress',
    bg: 'bg-indigo-50 dark:bg-indigo-950/40',
    text: 'text-indigo-700 dark:text-indigo-400',
    dot: 'bg-indigo-500',
  },
  'Blocked': {
    label: 'Blocked',
    bg: 'bg-rose-50 dark:bg-rose-950/40',
    text: 'text-rose-700 dark:text-rose-400',
    dot: 'bg-rose-500',
  },
  'Completed': {
    label: 'Completed',
    bg: 'bg-emerald-50 dark:bg-emerald-950/40',
    text: 'text-emerald-700 dark:text-emerald-400',
    dot: 'bg-emerald-500',
  },
  'Cancelled': {
    label: 'Cancelled',
    bg: 'bg-gray-100 dark:bg-gray-800',
    text: 'text-gray-500 dark:text-gray-400',
    dot: 'bg-gray-400',
  },
};

export const DECISION_STATUS_CONFIG: Record<
  DecisionStatus,
  { label: string; bg: string; text: string; border: string }
> = {
  Confirmed: {
    label: 'Confirmed',
    bg: 'bg-emerald-50 dark:bg-emerald-950/40',
    text: 'text-emerald-700 dark:text-emerald-400',
    border: 'border-emerald-200 dark:border-emerald-800',
  },
  Proposed: {
    label: 'Proposed',
    bg: 'bg-amber-50 dark:bg-amber-950/40',
    text: 'text-amber-700 dark:text-amber-400',
    border: 'border-amber-200 dark:border-amber-800',
  },
  Rejected: {
    label: 'Rejected',
    bg: 'bg-red-50 dark:bg-red-950/40',
    text: 'text-red-700 dark:text-red-400',
    border: 'border-red-200 dark:border-red-800',
  },
  Superseded: {
    label: 'Superseded',
    bg: 'bg-purple-50 dark:bg-purple-950/40',
    text: 'text-purple-700 dark:text-purple-400',
    border: 'border-purple-200 dark:border-purple-800',
  },
};
