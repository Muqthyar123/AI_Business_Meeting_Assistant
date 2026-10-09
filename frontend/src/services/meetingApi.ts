import { apiClient } from './apiClient';
import { Meeting } from '../types';

export const meetingApi = {
  getMeetings: async (): Promise<Meeting[]> => {
    const res = await apiClient.get<Meeting[]>('/api/meetings');
    return res.data;
  },

  getMeeting: async (meetingId: string): Promise<Meeting> => {
    const res = await apiClient.get<Meeting>(`/api/meetings/${meetingId}`);
    return res.data;
  },

  createMeeting: async (data: Partial<Meeting>): Promise<Meeting> => {
    const res = await apiClient.post<Meeting>('/api/meetings', data);
    return res.data;
  },

  updateMeeting: async (meetingId: string, data: Partial<Meeting>): Promise<Meeting> => {
    const res = await apiClient.patch<Meeting>(`/api/meetings/${meetingId}`, data);
    return res.data;
  },

  deleteMeeting: async (meetingId: string): Promise<void> => {
    await apiClient.delete(`/api/meetings/${meetingId}`);
  },
};
