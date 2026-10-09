import { apiClient } from './apiClient';

export interface ReportGenerationParams {
  meetingId?: string;
  startDate?: string;
  endDate?: string;
  department?: string;
  includeTranscript?: boolean;
  includeDecisions?: boolean;
  includeActionItems?: boolean;
  includeFollowUps?: boolean;
}

export const reportApi = {
  getReportData: async (params: ReportGenerationParams): Promise<any> => {
    try {
      const res = await apiClient.post('/api/reports/generate', params);
      return res.data;
    } catch {
      // Backend report endpoint not implemented yet, fallback to client assembly
      return null;
    }
  },
};
