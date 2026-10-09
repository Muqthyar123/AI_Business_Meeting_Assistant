import { apiClient } from './apiClient';

export interface DocumentResponse {
  id: string;
  source_type: 'pdf' | 'docx' | 'txt' | 'pasted_text';
  title?: string | null;
  original_filename?: string | null;
  file_format?: string | null;
  file_size_bytes?: number | null;
  text_content: string;
  character_count: number;
  word_count: number;
  status: 'completed' | 'failed';
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  items: DocumentResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const documentApi = {
  uploadDocument: async (file: File, title?: string): Promise<DocumentResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (title) {
      formData.append('title', title);
    }

    const res = await apiClient.post<DocumentResponse>('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  createPastedText: async (text: string, title?: string): Promise<DocumentResponse> => {
    const res = await apiClient.post<DocumentResponse>('/api/documents/text', {
      text,
      title: title || undefined,
    });
    return res.data;
  },

  getDocument: async (documentId: string): Promise<DocumentResponse> => {
    const res = await apiClient.get<DocumentResponse>(`/api/documents/${documentId}`);
    return res.data;
  },

  listDocuments: async (
    page = 1,
    pageSize = 20,
    sourceType?: string
  ): Promise<DocumentListResponse> => {
    const params: Record<string, any> = { page, page_size: pageSize };
    if (sourceType) params.source_type = sourceType;

    const res = await apiClient.get<DocumentListResponse>('/api/documents/', { params });
    return res.data;
  },

  deleteDocument: async (documentId: string): Promise<void> => {
    await apiClient.delete(`/api/documents/${documentId}`);
  },
};
