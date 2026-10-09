import { apiClient } from './apiClient';
import { BackendHealth } from '../types';

export const healthApi = {
  checkHealth: async (): Promise<BackendHealth> => {
    try {
      const response = await apiClient.get<BackendHealth>('/api/health', {
        timeout: 5000,
      });
      return {
        ...response.data,
        status: 'online',
        lastChecked: new Date().toISOString(),
      };
    } catch (error: any) {
      return {
        status: 'offline',
        lastChecked: new Date().toISOString(),
        message: error.message || 'Cannot reach FastAPI backend server',
      };
    }
  },
};
