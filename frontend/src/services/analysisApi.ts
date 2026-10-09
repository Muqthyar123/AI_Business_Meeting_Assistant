import { apiClient } from './apiClient';
import { Analysis } from '../types';

export interface AnalyzeOptions {
  focusAreas?: string[];
  customPrompt?: string;
}

export const analysisApi = {
  analyzeMeeting: async (
    meetingId: string,
    options?: AnalyzeOptions
  ): Promise<Analysis> => {
    const res = await apiClient.post<Analysis>(
      `/api/meetings/${meetingId}/analyze`,
      options || {}
    );
    return res.data;
  },

  getMeetingAnalysis: async (meetingId: string): Promise<Analysis> => {
    const res = await apiClient.get<Analysis>(`/api/meetings/${meetingId}/analysis`);
    return res.data;
  },
};
