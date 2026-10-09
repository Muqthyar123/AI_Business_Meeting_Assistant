import { apiClient } from './apiClient';
import { BackendTaskRecord } from './actionItemApi';

export interface BackendFollowUpPlanResponse {
  analysis_id: string;
  immediate_actions: BackendTaskRecord[];
  upcoming_tasks: BackendTaskRecord[];
  clarification_needed: BackendTaskRecord[];
  blockers_and_dependencies: BackendTaskRecord[];
  pending_decisions: string[];
  ai_suggestions: string[];
  total_tasks: number;
  generated_at: string;
}

export const followUpApi = {
  getFollowUpPlan: async (analysisId: string): Promise<BackendFollowUpPlanResponse> => {
    const res = await apiClient.get<BackendFollowUpPlanResponse>(
      `/api/tasks/analysis/${analysisId}/plan`
    );
    return res.data;
  },
};
