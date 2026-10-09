import { apiClient } from './apiClient';
import { ActionItem } from '../types';

export const actionItemApi = {
  getActionItems: async (meetingId?: string): Promise<ActionItem[]> => {
    const url = meetingId ? `/api/action-items?meeting_id=${meetingId}` : '/api/action-items';
    const res = await apiClient.get<ActionItem[]>(url);
    return res.data;
  },

  createActionItem: async (data: Partial<ActionItem>): Promise<ActionItem> => {
    const res = await apiClient.post<ActionItem>('/api/action-items', data);
    return res.data;
  },

  updateActionItem: async (
    taskId: string,
    data: Partial<ActionItem>
  ): Promise<ActionItem> => {
    const res = await apiClient.patch<ActionItem>(`/api/action-items/${taskId}`, data);
    return res.data;
  },

  deleteActionItem: async (taskId: string): Promise<void> => {
    await apiClient.delete(`/api/action-items/${taskId}`);
  },
};
