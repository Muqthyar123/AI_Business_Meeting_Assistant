import { Meeting } from '../types';
import { analysisApi, BackendAnalysisRecord } from './analysisApi';
import { transcriptionApi, BackendTranscriptionRecord } from './transcriptionApi';
import { documentApi, DocumentResponse } from './documentApi';
import { workflowApi } from './workflowApi';

export const meetingApi = {
  getMeetings: async (): Promise<Meeting[]> => {
    // Fetch analyses, transcriptions, and documents in parallel from backend
    const [analysesRes, transcriptionsRes, documentsRes] = await Promise.allSettled([
      analysisApi.listAnalyses(1, 100),
      transcriptionApi.listTranscriptions(1, 100),
      documentApi.listDocuments(1, 100),
    ]);

    const analyses = analysesRes.status === 'fulfilled' ? analysesRes.value.items : [];
    const transcriptions =
      transcriptionsRes.status === 'fulfilled' ? transcriptionsRes.value.items : [];
    const documents = documentsRes.status === 'fulfilled' ? documentsRes.value.items : [];

    const meetingsMap = new Map<string, Meeting>();

    // 1. Convert analyses into meetings
    for (const analysis of analyses) {
      const sourceTranscription = analysis.source_id
        ? transcriptions.find((t) => t.id === analysis.source_id)
        : undefined;
      const sourceDoc = analysis.source_id
        ? documents.find((d) => d.id === analysis.source_id)
        : undefined;

      const duration = sourceTranscription?.audio_duration
        ? Math.round(sourceTranscription.audio_duration)
        : 900;

      const meeting: Meeting = {
        id: analysis.id,
        title:
          analysis.title ||
          sourceDoc?.title ||
          sourceTranscription?.original_filename?.replace(/\.[^/.]+$/, '') ||
          'Executive Meeting',
        description: analysis.meeting_purpose || analysis.executive_summary?.slice(0, 150),
        meetingDate: analysis.created_at,
        durationSeconds: duration,
        participants: ['Team'],
        meetingType: 'Team Meeting',
        department: analysis.topics_and_themes?.[0] || 'General',
        status: 'ready',
        transcriptionId: analysis.source_type === 'transcription' ? analysis.source_id || undefined : undefined,
        analysisStatus: analysis.status === 'completed' ? 'completed' : 'failed',
        audioFilename: sourceTranscription?.original_filename || undefined,
        createdAt: analysis.created_at,
        updatedAt: analysis.updated_at,
      };

      meetingsMap.set(meeting.id, meeting);
    }

    // 2. Add transcriptions that might not have an analysis yet
    for (const tr of transcriptions) {
      // Check if an analysis already referenced this transcription
      const hasAnalysis = analyses.some(
        (a) => a.source_id === tr.id && a.source_type === 'transcription'
      );
      if (!hasAnalysis) {
        const meetingStatus =
          tr.status === 'completed'
            ? 'ready'
            : tr.status === 'processing'
            ? 'processing'
            : tr.status === 'failed'
            ? 'failed'
            : 'queued';

        const meeting: Meeting = {
          id: tr.id,
          title: tr.original_filename.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' '),
          description: `Uploaded audio recording (${tr.file_format.toUpperCase()})`,
          meetingDate: tr.created_at,
          durationSeconds: tr.audio_duration ? Math.round(tr.audio_duration) : 600,
          participants: ['Speakers'],
          meetingType: 'Project Review',
          department: 'Audio Uploads',
          status: meetingStatus,
          transcriptionId: tr.id,
          analysisStatus: 'none',
          audioFilename: tr.original_filename,
          createdAt: tr.created_at,
          updatedAt: tr.updated_at,
        };
        meetingsMap.set(meeting.id, meeting);
      }
    }

    // 3. Add standalone documents not analyzed yet
    for (const doc of documents) {
      const hasAnalysis = analyses.some(
        (a) => a.source_id === doc.id && (a.source_type === 'document' || a.source_type === 'pasted_text')
      );
      if (!hasAnalysis) {
        const meeting: Meeting = {
          id: doc.id,
          title: doc.title || doc.original_filename || 'Ingested Meeting Notes',
          description: doc.text_content.slice(0, 150),
          meetingDate: doc.created_at,
          durationSeconds: Math.max(300, Math.floor(doc.word_count * 0.4)),
          participants: ['Attendees'],
          meetingType: 'Planning',
          department: 'Documents',
          status: 'ready',
          analysisStatus: 'none',
          createdAt: doc.created_at,
          updatedAt: doc.updated_at,
        };
        meetingsMap.set(meeting.id, meeting);
      }
    }

    return Array.from(meetingsMap.values()).sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  },

  getMeeting: async (meetingId: string): Promise<Meeting | undefined> => {
    // Try analysis first
    try {
      const analysis = await analysisApi.getAnalysis(meetingId);
      return {
        id: analysis.id,
        title: analysis.title || 'Executive Meeting',
        description: analysis.meeting_purpose || analysis.executive_summary?.slice(0, 150),
        meetingDate: analysis.created_at,
        durationSeconds: 900,
        participants: ['Team'],
        meetingType: 'Team Meeting',
        department: analysis.topics_and_themes?.[0] || 'General',
        status: 'ready',
        transcriptionId: analysis.source_type === 'transcription' ? analysis.source_id || undefined : undefined,
        analysisStatus: analysis.status === 'completed' ? 'completed' : 'failed',
        createdAt: analysis.created_at,
        updatedAt: analysis.updated_at,
      };
    } catch {
      // Try transcription
      try {
        const tr = await transcriptionApi.getTranscription(meetingId);
        return {
          id: tr.id,
          title: tr.original_filename.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' '),
          description: `Uploaded audio (${tr.file_format.toUpperCase()})`,
          meetingDate: tr.created_at,
          durationSeconds: tr.audio_duration ? Math.round(tr.audio_duration) : 600,
          participants: ['Speakers'],
          meetingType: 'Project Review',
          department: 'Audio Uploads',
          status: tr.status === 'completed' ? 'ready' : (tr.status as any),
          transcriptionId: tr.id,
          analysisStatus: 'none',
          audioFilename: tr.original_filename,
          createdAt: tr.created_at,
          updatedAt: tr.updated_at,
        };
      } catch {
        // Try document
        try {
          const doc = await documentApi.getDocument(meetingId);
          return {
            id: doc.id,
            title: doc.title || doc.original_filename || 'Ingested Meeting Notes',
            description: doc.text_content.slice(0, 150),
            meetingDate: doc.created_at,
            durationSeconds: Math.max(300, Math.floor(doc.word_count * 0.4)),
            participants: ['Attendees'],
            meetingType: 'Planning',
            department: 'Documents',
            status: 'ready',
            analysisStatus: 'none',
            createdAt: doc.created_at,
            updatedAt: doc.updated_at,
          };
        } catch {
          return undefined;
        }
      }
    }
  },

  createMeeting: async (data: Partial<Meeting> & { text?: string }): Promise<Meeting> => {
    // If text or description provided, create as pasted text document
    const title = data.title || 'Executive Meeting';
    const textContent = data.text || data.description || 'Meeting notes initiated.';

    const doc = await documentApi.createPastedText(textContent, title);
    return {
      id: doc.id,
      title: doc.title || title,
      description: doc.text_content.slice(0, 150),
      meetingDate: data.meetingDate || doc.created_at,
      durationSeconds: data.durationSeconds || Math.max(300, Math.floor(doc.word_count * 0.4)),
      participants: data.participants || ['Team'],
      meetingType: data.meetingType || 'Team Meeting',
      department: data.department || 'General',
      status: 'ready',
      analysisStatus: 'none',
      createdAt: doc.created_at,
      updatedAt: doc.updated_at,
    };
  },

  updateMeeting: async (meetingId: string, data: Partial<Meeting>): Promise<Meeting | undefined> => {
    const existing = await meetingApi.getMeeting(meetingId);
    if (!existing) return undefined;
    return {
      ...existing,
      ...data,
      updatedAt: new Date().toISOString(),
    };
  },

  deleteMeeting: async (meetingId: string): Promise<void> => {
    // Attempt deleting from analysis, transcription, document, or workflow
    await Promise.allSettled([
      analysisApi.deleteAnalysis(meetingId),
      transcriptionApi.deleteTranscription(meetingId),
      documentApi.deleteDocument(meetingId),
      workflowApi.deleteWorkflow(meetingId),
    ]);
  },
};
