import { apiClient } from './apiClient';

export type BackendTaskPriority = 'low' | 'medium' | 'high' | 'unknown';
export type BackendTaskStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';

export interface BackendTaskRecord {
  id: string;
  analysis_id: string;
  description: string;
  assignee?: string | null;
  has_missing_assignee: boolean;
  due_date?: string | null;
  priority: BackendTaskPriority;
  status: BackendTaskStatus;
  dependencies: string[];
  evidence_excerpt?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  items: BackendTaskRecord[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TaskCreatePayload {
  analysis_id: string;
  description: string;
  assignee?: string | null;
  has_missing_assignee?: boolean;
  due_date?: string | null;
  priority?: BackendTaskPriority;
  status?: BackendTaskStatus;
  dependencies?: string[];
  evidence_excerpt?: string | null;
}

export interface TaskUpdatePayload {
  description?: string;
  assignee?: string | null;
  has_missing_assignee?: boolean;
  due_date?: string | null;
  priority?: BackendTaskPriority;
  status?: BackendTaskStatus;
  dependencies?: string[];
  evidence_excerpt?: string | null;
}

export const actionItemApi = {
  extractActionItems: async (
    analysisId: string,
    replace = true
  ): Promise<BackendTaskRecord[]> => {
    const res = await apiClient.post<BackendTaskRecord[]>(
      `/api/tasks/extract/${analysisId}`,
      null,
      {
        params: { replace },
      }
    );
    return res.data;
  },

  createActionItem: async (payload: TaskCreatePayload): Promise<BackendTaskRecord> => {
    const res = await apiClient.post<BackendTaskRecord>('/api/tasks/', payload);
    return res.data;
  },

  getActionItems: async (params?: {
    analysis_id?: string;
    status?: string;
    priority?: string;
    assignee?: string;
    page?: number;
    page_size?: number;
  }): Promise<TaskListResponse> => {
    const res = await apiClient.get<TaskListResponse>('/api/tasks/', {
      params: {
        page: params?.page || 1,
        page_size: params?.page_size || 100,
        analysis_id: params?.analysis_id,
        status: params?.status,
        priority: params?.priority,
        assignee: params?.assignee,
      },
    });
    return res.data;
  },

  getActionItem: async (taskId: string): Promise<BackendTaskRecord> => {
    const res = await apiClient.get<BackendTaskRecord>(`/api/tasks/${taskId}`);
    return res.data;
  },

  updateActionItem: async (
    taskId: string,
    payload: TaskUpdatePayload
  ): Promise<BackendTaskRecord> => {
    const res = await apiClient.patch<BackendTaskRecord>(`/api/tasks/${taskId}`, payload);
    return res.data;
  },

  updateActionItemStatus: async (
    taskId: string,
    status: BackendTaskStatus
  ): Promise<BackendTaskRecord> => {
    const res = await apiClient.patch<BackendTaskRecord>(`/api/tasks/${taskId}/status`, {
      status,
    });
    return res.data;
  },

  deleteActionItem: async (taskId: string): Promise<void> => {
    await apiClient.delete(`/api/tasks/${taskId}`);
  },

  exportTasks: async (
    analysisId?: string,
    format: 'json' | 'csv' | 'markdown' = 'json'
  ): Promise<Blob> => {
    const res = await apiClient.get('/api/tasks/export', {
      params: { format, analysis_id: analysisId },
      responseType: 'blob',
    });
    return res.data;
  },
};
