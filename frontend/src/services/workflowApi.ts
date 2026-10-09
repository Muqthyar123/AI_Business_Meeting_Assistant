import { apiClient } from './apiClient';

export interface WorkflowStartPayload {
  source_type: 'transcription' | 'document' | 'direct_text' | 'pasted_text';
  source_id?: string | null;
  text?: string | null;
  title?: string | null;
  force_reanalyze?: boolean;
}

export interface WorkflowStatusResponse {
  id: string;
  source_type: string;
  source_id?: string | null;
  title?: string | null;
  current_stage: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  analysis_id?: string | null;
  error_stage?: string | null;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  updated_at: string;
  completed_at?: string | null;
}

export interface WorkflowResultResponse {
  id: string;
  source_type: string;
  source_id?: string | null;
  title?: string | null;
  current_stage: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  analysis?: any;
  tasks: any[];
  follow_up_plan?: any;
  error_stage?: string | null;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  updated_at: string;
  completed_at?: string | null;
}

export interface WorkflowListResponse {
  items: WorkflowStatusResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const workflowApi = {
  startWorkflow: async (payload: WorkflowStartPayload): Promise<WorkflowStatusResponse> => {
    const res = await apiClient.post<WorkflowStatusResponse>('/api/workflows/start', payload);
    return res.data;
  },

  runSyncWorkflow: async (payload: WorkflowStartPayload): Promise<WorkflowResultResponse> => {
    const res = await apiClient.post<WorkflowResultResponse>('/api/workflows/run-sync', payload);
    return res.data;
  },

  getWorkflowStatus: async (workflowId: string): Promise<WorkflowStatusResponse> => {
    const res = await apiClient.get<WorkflowStatusResponse>(`/api/workflows/${workflowId}`);
    return res.data;
  },

  getWorkflowResult: async (workflowId: string): Promise<WorkflowResultResponse> => {
    const res = await apiClient.get<WorkflowResultResponse>(`/api/workflows/${workflowId}/result`);
    return res.data;
  },

  retryWorkflow: async (workflowId: string): Promise<WorkflowStatusResponse> => {
    const res = await apiClient.post<WorkflowStatusResponse>(`/api/workflows/${workflowId}/retry`);
    return res.data;
  },

  listWorkflows: async (page = 1, pageSize = 20): Promise<WorkflowListResponse> => {
    const res = await apiClient.get<WorkflowListResponse>('/api/workflows/', {
      params: { page, page_size: pageSize },
    });
    return res.data;
  },

  deleteWorkflow: async (workflowId: string): Promise<void> => {
    await apiClient.delete(`/api/workflows/${workflowId}`);
  },

  pollWorkflow: async (
    workflowId: string,
    onProgress?: (stage: string, status: string) => void,
    maxAttempts = 60,
    delayMs = 2000
  ): Promise<WorkflowResultResponse> => {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const statusRes = await workflowApi.getWorkflowStatus(workflowId);
      if (onProgress) {
        onProgress(statusRes.current_stage, statusRes.status);
      }

      if (statusRes.status === 'completed') {
        return await workflowApi.getWorkflowResult(workflowId);
      }

      if (statusRes.status === 'failed') {
        throw new Error(statusRes.error_message || `Workflow failed at stage ${statusRes.error_stage}`);
      }

      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    throw new Error('Workflow execution timed out while polling.');
  },
};
