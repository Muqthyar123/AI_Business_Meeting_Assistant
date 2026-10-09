import { apiClient } from './apiClient';
import { BackendHealth } from '../types';

export interface RawHealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  api_status: string;
  database_status: 'connected' | 'disconnected';
  whisper_status: 'loaded' | 'not_loaded' | 'unavailable';
  whisper_model?: string | null;
  version: string;
  timestamp: string;
}

export const healthApi = {
  checkHealth: async (): Promise<BackendHealth> => {
    try {
      const response = await apiClient.get<RawHealthResponse>('/api/health', {
        timeout: 6000,
      });
      const data = response.data;
      const isHealthy = data.status === 'healthy' || data.database_status === 'connected';

      return {
        status: isHealthy ? 'online' : 'degraded',
        version: data.version,
        whisperAvailable: data.whisper_status === 'loaded',
        groqAvailable: true,
        langGraphAvailable: true,
        databaseConnected: data.database_status === 'connected',
        lastChecked: data.timestamp || new Date().toISOString(),
        message: `FastAPI backend active (DB: ${data.database_status}, Whisper: ${data.whisper_status})`,
      };
    } catch (error: any) {
      return {
        status: 'offline',
        whisperAvailable: false,
        groqAvailable: false,
        langGraphAvailable: false,
        databaseConnected: false,
        lastChecked: new Date().toISOString(),
        message: error.message || 'Cannot reach FastAPI backend server',
      };
    }
  },
};
