import { apiClient } from './apiClient';

export interface UploadAudioParams {
  file: File;
  language?: string;
  onUploadProgress?: (progressEvent: { loaded: number; total?: number }) => void;
}

export interface TranscriptionCreateResponse {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  message: string;
}

export interface BackendTranscriptionRecord {
  id: string;
  original_filename: string;
  file_format: string;
  file_size_bytes: number;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  audio_duration?: number | null;
  requested_language?: string | null;
  detected_language?: string | null;
  whisper_model: string;
  transcript_text?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface BackendTranscriptionListResponse {
  items: BackendTranscriptionRecord[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const transcriptionApi = {
  uploadAudio: async ({
    file,
    language,
    onUploadProgress,
  }: UploadAudioParams): Promise<TranscriptionCreateResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (language && language !== 'auto') {
      formData.append('language', language);
    }

    const res = await apiClient.post<TranscriptionCreateResponse>(
      '/api/transcriptions/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onUploadProgress && progressEvent.total) {
            onUploadProgress({ loaded: progressEvent.loaded, total: progressEvent.total });
          }
        },
      }
    );
    return res.data;
  },

  getTranscription: async (transcriptionId: string): Promise<BackendTranscriptionRecord> => {
    const res = await apiClient.get<BackendTranscriptionRecord>(
      `/api/transcriptions/${transcriptionId}`
    );
    return res.data;
  },

  listTranscriptions: async (
    page = 1,
    pageSize = 20,
    status?: string
  ): Promise<BackendTranscriptionListResponse> => {
    const params: Record<string, any> = { page, page_size: pageSize };
    if (status) params.status = status;

    const res = await apiClient.get<BackendTranscriptionListResponse>('/api/transcriptions/', {
      params,
    });
    return res.data;
  },

  updateTranscription: async (
    transcriptionId: string,
    transcriptText: string
  ): Promise<BackendTranscriptionRecord> => {
    const res = await apiClient.patch<BackendTranscriptionRecord>(
      `/api/transcriptions/${transcriptionId}`,
      { transcript_text: transcriptText }
    );
    return res.data;
  },

  deleteTranscription: async (transcriptionId: string): Promise<void> => {
    await apiClient.delete(`/api/transcriptions/${transcriptionId}`);
  },

  pollTranscription: async (
    transcriptionId: string,
    onStatusChange?: (status: string) => void,
    maxAttempts = 120,
    delayMs = 1500
  ): Promise<BackendTranscriptionRecord> => {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const record = await transcriptionApi.getTranscription(transcriptionId);
      if (onStatusChange) {
        onStatusChange(record.status);
      }

      if (record.status === 'completed') {
        return record;
      }

      if (record.status === 'failed') {
        throw new Error(record.error_message || 'Audio transcription failed on the backend.');
      }

      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    throw new Error('Transcription processing timed out.');
  },
};
