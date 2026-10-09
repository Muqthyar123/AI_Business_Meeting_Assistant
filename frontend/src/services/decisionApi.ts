import { apiClient } from './apiClient';
import { Decision } from '../types';

export const decisionApi = {
  getDecisions: async (meetingId?: string): Promise<Decision[]> => {
    const url = meetingId ? `/api/meetings/${meetingId}/decisions` : '/api/decisions';
    const res = await apiClient.get<Decision[]>(url);
    return res.data;
  },

  createDecision: async (data: Partial<Decision>): Promise<Decision> => {
    const res = await apiClient.post<Decision>('/api/decisions', data);
    return res.data;
  },

  updateDecision: async (
    decisionId: string,
    data: Partial<Decision>
  ): Promise<Decision> => {
    const res = await apiClient.patch<Decision>(`/api/decisions/${decisionId}`, data);
    return res.data;
  },

  deleteDecision: async (decisionId: string): Promise<void> => {
    await apiClient.delete(`/api/decisions/${decisionId}`);
  },
};
