import { apiClient } from './apiClient';
import { Transcript } from '../types';

export interface UploadAudioParams {
  file: File;
  meetingId?: string;
  language?: string;
  model?: string;
  onUploadProgress?: (progressEvent: { loaded: number; total?: number }) => void;
}

export const transcriptionApi = {
  uploadAudio: async ({
    file,
    meetingId,
    language,
    model,
    onUploadProgress,
  }: UploadAudioParams): Promise<Transcript> => {
    const formData = new FormData();
    formData.append('file', file);
    if (meetingId) formData.append('meeting_id', meetingId);
    if (language) formData.append('language', language);
    if (model) formData.append('model', model);

    const res = await apiClient.post<Transcript>('/api/transcriptions', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          onUploadProgress({ loaded: progressEvent.loaded, total: progressEvent.total });
        }
      },
    });
    return res.data;
  },

  getTranscription: async (transcriptionId: string): Promise<Transcript> => {
    const res = await apiClient.get<Transcript>(`/api/transcriptions/${transcriptionId}`);
    return res.data;
  },

  updateTranscription: async (
    transcriptionId: string,
    updates: Partial<Transcript>
  ): Promise<Transcript> => {
    const res = await apiClient.patch<Transcript>(
      `/api/transcriptions/${transcriptionId}`,
      updates
    );
    return res.data;
  },

  deleteTranscription: async (transcriptionId: string): Promise<void> => {
    await apiClient.delete(`/api/transcriptions/${transcriptionId}`);
  },
};
