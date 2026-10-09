import { apiClient } from './apiClient';

export interface AnalysisCreatePayload {
  source_type: 'transcription' | 'document' | 'direct_text' | 'pasted_text';
  source_id?: string | null;
  text?: string | null;
  title?: string | null;
}

export interface BackendAnalysisRecord {
  id: string;
  source_id?: string | null;
  source_type: string;
  title?: string | null;
  executive_summary: string;
  meeting_purpose: string;
  key_discussion_points: string[];
  decisions_made: string[];
  risks_and_blockers: string[];
  unresolved_questions: string[];
  topics_and_themes: string[];
  llm_provider: string;
  llm_model: string;
  status: 'completed' | 'failed';
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AnalysisListResponse {
  items: BackendAnalysisRecord[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const analysisApi = {
  createAnalysis: async (payload: AnalysisCreatePayload): Promise<BackendAnalysisRecord> => {
    const res = await apiClient.post<BackendAnalysisRecord>('/api/analysis/', payload);
    return res.data;
  },

  getAnalysis: async (analysisId: string): Promise<BackendAnalysisRecord> => {
    const res = await apiClient.get<BackendAnalysisRecord>(`/api/analysis/${analysisId}`);
    return res.data;
  },

  listAnalyses: async (
    page = 1,
    pageSize = 20,
    sourceType?: string
  ): Promise<AnalysisListResponse> => {
    const params: Record<string, any> = { page, page_size: pageSize };
    if (sourceType) params.source_type = sourceType;

    const res = await apiClient.get<AnalysisListResponse>('/api/analysis/', { params });
    return res.data;
  },

  deleteAnalysis: async (analysisId: string): Promise<void> => {
    await apiClient.delete(`/api/analysis/${analysisId}`);
  },
};
