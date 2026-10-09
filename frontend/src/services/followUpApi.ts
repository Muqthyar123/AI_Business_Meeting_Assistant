import { apiClient } from './apiClient';
import { FollowUpPlan } from '../types';

export const followUpApi = {
  getFollowUps: async (meetingId?: string): Promise<FollowUpPlan[]> => {
    const url = meetingId ? `/api/meetings/${meetingId}/follow-up` : '/api/follow-ups';
    const res = await apiClient.get<FollowUpPlan[] | FollowUpPlan>(url);
    if (Array.isArray(res.data)) {
      return res.data;
    }
    return res.data ? [res.data] : [];
  },

  generateFollowUp: async (meetingId: string): Promise<FollowUpPlan> => {
    const res = await apiClient.post<FollowUpPlan>(`/api/meetings/${meetingId}/follow-up`);
    return res.data;
  },

  updateFollowUp: async (
    planId: string,
    data: Partial<FollowUpPlan>
  ): Promise<FollowUpPlan> => {
    const res = await apiClient.patch<FollowUpPlan>(`/api/follow-ups/${planId}`, data);
    return res.data;
  },

  deleteFollowUp: async (planId: string): Promise<void> => {
    await apiClient.delete(`/api/follow-ups/${planId}`);
  },
};
