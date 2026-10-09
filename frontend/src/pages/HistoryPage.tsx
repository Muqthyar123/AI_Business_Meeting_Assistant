import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  History as HistoryIcon,
  Search,
  Download,
  Calendar,
  Clock,
  CheckCircle2,
  ListTodo,
  ExternalLink,
  Trash2,
  FileText,
  Filter,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import { formatDateTime, formatDuration } from '../utils/formatters';
import { exportMeetingAsPdf, exportAsTxt } from '../utils/exportHelpers';
import { useData } from '../context/DataContext';
import { toast } from 'sonner';

export const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const { meetings, decisions, actionItems, followUps, getTranscript, getAnalysis, deleteMeeting } =
    useData();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 6;

  const filteredHistory = useMemo(() => {
    return meetings.filter((m) => {
      const matchesSearch =
        m.title.toLowerCase().includes(search.toLowerCase()) ||
        (m.audioFilename && m.audioFilename.toLowerCase().includes(search.toLowerCase())) ||
        m.participants.some((p) => p.toLowerCase().includes(search.toLowerCase()));

      const matchesStatus =
        statusFilter === 'all' ||
        (statusFilter === 'analyzed' && m.analysisStatus === 'completed') ||
        (statusFilter === 'not-analyzed' && m.analysisStatus !== 'completed');

      return matchesSearch && matchesStatus;
    });
  }, [meetings, search, statusFilter]);

  const totalPages = Math.ceil(filteredHistory.length / itemsPerPage) || 1;
  const paginatedMeetings = filteredHistory.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const handleDownloadTranscript = async (e: React.MouseEvent, meetingId: string, title: string) => {
    e.stopPropagation();
    const t = await getTranscript(meetingId);
    if (t?.text) {
      exportAsTxt(t.text, `${title.replace(/[^a-zA-Z0-9_-]/g, '_')}_transcript.txt`);
      toast.success('Downloaded transcript TXT');
    } else {
      toast.error('No transcript text available for download');
    }
  };

  const handleExportPdf = async (e: React.MouseEvent, m: any) => {
    e.stopPropagation();
    const [t, a] = await Promise.all([getTranscript(m.id), getAnalysis(m.id)]);
    const decs = decisions.filter((d) => d.meetingId === m.id);
    const acts = actionItems.filter((a) => a.meetingId === m.id);
    const flw = followUps.find((f) => f.meetingId === m.id);

    exportMeetingAsPdf(m, a, decs, acts, flw);
    toast.success('PDF report exported');
  };

  const handleDelete = (e: React.MouseEvent, id: string, title: string) => {
    e.stopPropagation();
    if (window.confirm(`Permanently remove "${title}" from meeting history?`)) {
      deleteMeeting(id);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-content-primary dark:text-content-darkPrimary flex items-center gap-2.5">
            <HistoryIcon className="w-6 h-6 text-brand-primary" />
            Meeting History & Audit Archive
          </h1>
          <p className="text-xs sm:text-sm text-content-secondary dark:text-content-darkSecondary mt-0.5">
            Complete archive of transcribed recordings, analysis versions, and historical outcomes
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-content-secondary absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search history by audio filename, title, or participant..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-xl border border-edge-light dark:border-edge-dark bg-surface-secondary/40 text-xs sm:text-sm text-content-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs px-3 py-2 rounded-xl border border-edge-light dark:border-edge-dark bg-white dark:bg-surface-darkSecondary text-content-primary focus:outline-none"
            >
              <option value="all">All Processing States</option>
              <option value="analyzed">AI Analyzed</option>
              <option value="not-analyzed">Needs Analysis</option>
            </select>
          </div>
        </div>
      </Card>

      {/* History Table */}
      {paginatedMeetings.length === 0 ? (
        <EmptyState
          icon={<HistoryIcon className="w-8 h-8 text-brand-primary" />}
          title="No archived meetings"
          description={
            search
              ? `No records match "${search}".`
              : 'Your meeting history is currently empty. Audio recordings processed through Whisper will appear here.'
          }
          actionLabel="Upload Audio"
          onAction={() => navigate('/meetings/new')}
        />
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="border-b border-edge-light dark:border-edge-dark bg-surface-secondary/40 dark:bg-surface-darkSecondary/30 text-[11px] font-semibold uppercase tracking-wider text-content-secondary">
                  <th className="py-3 px-4 sm:px-6">Meeting & File</th>
                  <th className="py-3 px-3">Date Recorded</th>
                  <th className="py-3 px-3">Audio Length</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3 text-center">Decisions</th>
                  <th className="py-3 px-3 text-center">Tasks</th>
                  <th className="py-3 px-4 sm:px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-edge-light dark:divide-edge-dark">
                {paginatedMeetings.map((m) => {
                  const decCount = decisions.filter((d) => d.meetingId === m.id).length;
                  const actCount = actionItems.filter((a) => a.meetingId === m.id).length;

                  return (
                    <tr
                      key={m.id}
                      onClick={() => navigate(`/meetings/${m.id}`)}
                      className="hover:bg-surface-secondary/40 dark:hover:bg-surface-darkSecondary/30 cursor-pointer transition-colors group"
                    >
                      <td className="py-3.5 px-4 sm:px-6">
                        <div>
                          <p className="font-semibold text-content-primary dark:text-content-darkPrimary group-hover:text-brand-primary transition-colors">
                            {m.title}
                          </p>
                          <p className="text-xs text-content-secondary font-mono mt-0.5">
                            {m.audioFilename || 'audio_stream.mp3'}
                          </p>
                        </div>
                      </td>

                      <td className="py-3.5 px-3 text-xs text-content-secondary whitespace-nowrap">
                        {formatDateTime(m.meetingDate)}
                      </td>

                      <td className="py-3.5 px-3 text-xs text-content-secondary whitespace-nowrap">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          {formatDuration(m.durationSeconds)}
                        </span>
                      </td>

                      <td className="py-3.5 px-3 whitespace-nowrap">
                        {m.analysisStatus === 'completed' ? (
                          <Badge variant="indigo" size="sm" dot>
                            Completed
                          </Badge>
                        ) : (
                          <Badge variant="neutral" size="sm">
                            Ready
                          </Badge>
                        )}
                      </td>

                      <td className="py-3.5 px-3 text-center whitespace-nowrap">
                        <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-full border border-emerald-200">
                          {decCount}
                        </span>
                      </td>

                      <td className="py-3.5 px-3 text-center whitespace-nowrap">
                        <span className="text-xs font-semibold text-brand-primary dark:text-brand-secondary bg-brand-light dark:bg-brand-primary/20 px-2 py-0.5 rounded-full border border-brand-primary/20">
                          {actCount}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 sm:px-6 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 px-2"
                            onClick={(e) => handleDownloadTranscript(e, m.id, m.title)}
                            title="Download Transcript TXT"
                          >
                            <FileText className="w-3.5 h-3.5" />
                          </Button>

                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 px-2"
                            onClick={(e) => handleExportPdf(e, m)}
                            title="Export PDF Report"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </Button>

                          <button
                            onClick={(e) => handleDelete(e, m.id, m.title)}
                            className="p-1.5 rounded-lg text-content-secondary hover:text-rose-600 hover:bg-rose-50 transition-colors"
                            title="Delete record"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination Bar */}
          {totalPages > 1 && (
            <div className="px-6 py-3 border-t border-edge-light dark:border-edge-dark flex items-center justify-between text-xs text-content-secondary">
              <span>
                Showing {(currentPage - 1) * itemsPerPage + 1} to{' '}
                {Math.min(currentPage * itemsPerPage, filteredHistory.length)} of{' '}
                {filteredHistory.length} meetings
              </span>

              <div className="flex items-center gap-1.5">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <span className="px-2 font-medium">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};
