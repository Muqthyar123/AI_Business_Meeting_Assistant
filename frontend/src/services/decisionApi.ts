import { apiClient } from './apiClient';
import { Decision } from '../types';
import { analysisApi } from './analysisApi';

export const decisionApi = {
  getDecisions: async (analysisId?: string): Promise<Decision[]> => {
    if (analysisId) {
      try {
        const analysis = await analysisApi.getAnalysis(analysisId);
        return (analysis.decisions_made || []).map((text, idx) => ({
          id: `${analysis.id}-dec-${idx + 1}`,
          meetingId: analysis.id,
          meetingTitle: analysis.title || 'Meeting Analysis',
          title: text,
          description: text,
          owner: 'Executive Team',
          status: 'Confirmed' as const,
          category: 'Strategy & Execution',
          createdAt: analysis.created_at,
          updatedAt: analysis.updated_at,
        }));
      } catch {
        return [];
      }
    }

    // Otherwise fetch all analyses and collect decisions
    try {
      const analyses = await analysisApi.listAnalyses(1, 100);
      const allDecisions: Decision[] = [];
      for (const a of analyses.items) {
        if (a.decisions_made && a.decisions_made.length > 0) {
          a.decisions_made.forEach((text, idx) => {
            allDecisions.push({
              id: `${a.id}-dec-${idx + 1}`,
              meetingId: a.id,
              meetingTitle: a.title || 'Meeting Analysis',
              title: text,
              description: text,
              owner: 'Executive Team',
              status: 'Confirmed' as const,
              category: 'Strategy & Execution',
              createdAt: a.created_at,
              updatedAt: a.updated_at,
            });
          });
        }
      }
      return allDecisions;
    } catch {
      return [];
    }
  },

  createDecision: async (data: Partial<Decision>): Promise<Decision> => {
    const newDecision: Decision = {
      id: `dec-${Date.now().toString(36)}`,
      meetingId: data.meetingId || 'global',
      meetingTitle: data.meetingTitle || 'Manual Entry',
      title: data.title || 'Recorded Decision',
      description: data.description || data.title || '',
      owner: data.owner || 'Executive Team',
      status: data.status || 'Confirmed',
      category: data.category || 'Operations',
      evidence: data.evidence,
      isManual: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    return newDecision;
  },

  updateDecision: async (
    decisionId: string,
    data: Partial<Decision>
  ): Promise<Decision> => {
    return {
      id: decisionId,
      meetingId: data.meetingId || 'global',
      title: data.title || '',
      description: data.description || '',
      status: data.status || 'Confirmed',
      createdAt: data.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      ...data,
    };
  },

  deleteDecision: async (_decisionId: string): Promise<void> => {
    // Client-side delete handler
  },
};
