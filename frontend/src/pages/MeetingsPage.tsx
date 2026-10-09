import React, { useState, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Calendar,
  Clock,
  Plus,
  Search,
  Filter,
  LayoutGrid,
  List,
  Sparkles,
  CheckCircle2,
  ListTodo,
  MoreHorizontal,
  Trash2,
  FileText,
  Users,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Input, Select } from '../components/ui/Input';
import { EmptyState } from '../components/ui/EmptyState';
import { formatDateTime, formatDuration } from '../utils/formatters';
import { MEETING_TYPES } from '../config/constants';
import { useData } from '../context/DataContext';

export const MeetingsPage: React.FC = () => {
  const navigate = useNavigate();
  const { meetings, deleteMeeting, decisions, actionItems } = useData();

  const [search, setSearch] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [sortBy, setSortBy] = useState<'date-desc' | 'date-asc' | 'title'>('date-desc');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const filteredMeetings = useMemo(() => {
    return meetings
      .filter((m) => {
        const matchesSearch =
          m.title.toLowerCase().includes(search.toLowerCase()) ||
          (m.description && m.description.toLowerCase().includes(search.toLowerCase())) ||
          m.participants.some((p) => p.toLowerCase().includes(search.toLowerCase()));

        const matchesType = selectedType === 'all' || m.meetingType === selectedType;
        const matchesStatus =
          selectedStatus === 'all' ||
          (selectedStatus === 'analyzed' && m.analysisStatus === 'completed') ||
          (selectedStatus === 'not-analyzed' && m.analysisStatus !== 'completed');

        return matchesSearch && matchesType && matchesStatus;
      })
      .sort((a, b) => {
        if (sortBy === 'date-desc') {
          return new Date(b.meetingDate).getTime() - new Date(a.meetingDate).getTime();
        }
        if (sortBy === 'date-asc') {
          return new Date(a.meetingDate).getTime() - new Date(b.meetingDate).getTime();
        }
        if (sortBy === 'title') {
          return a.title.localeCompare(b.title);
        }
        return 0;
      });
  }, [meetings, search, selectedType, selectedStatus, sortBy]);

  const handleDeleteMeeting = (e: React.MouseEvent, id: string, title: string) => {
    e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete meeting "${title}" and its associated transcripts and decisions?`)) {
      deleteMeeting(id);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-content-primary dark:text-content-darkPrimary">
            Meetings Workspace
          </h1>
          <p className="text-xs sm:text-sm text-content-secondary dark:text-content-darkSecondary mt-0.5">
            Manage audio recordings, transcripts, AI insights, and executive summaries
          </p>
        </div>

        <Button
          variant="primary"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => navigate('/meetings/new')}
        >
          New Meeting
        </Button>
      </div>

      {/* Search & Filter Toolbar */}
      <Card className="p-4">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-content-secondary absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search meetings by title, description, or attendee..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-xl border border-edge-light dark:border-edge-dark bg-surface-secondary/40 text-xs sm:text-sm text-content-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2 w-full lg:w-auto">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="text-xs px-3 py-2 rounded-xl border border-edge-light dark:border-edge-dark bg-white dark:bg-surface-darkSecondary text-content-primary focus:outline-none"
            >
              <option value="all">All Meeting Types</option>
              {MEETING_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>

            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="text-xs px-3 py-2 rounded-xl border border-edge-light dark:border-edge-dark bg-white dark:bg-surface-darkSecondary text-content-primary focus:outline-none"
            >
              <option value="all">All AI Statuses</option>
              <option value="analyzed">Analyzed with AI</option>
              <option value="not-analyzed">Needs Analysis</option>
            </select>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="text-xs px-3 py-2 rounded-xl border border-edge-light dark:border-edge-dark bg-white dark:bg-surface-darkSecondary text-content-primary focus:outline-none"
            >
              <option value="date-desc">Newest First</option>
              <option value="date-asc">Oldest First</option>
              <option value="title">Alphabetical (Title)</option>
            </select>

            <div className="flex rounded-xl border border-edge-light dark:border-edge-dark p-0.5 bg-surface-secondary/40">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-1.5 rounded-lg transition-colors ${
                  viewMode === 'grid'
                    ? 'bg-white dark:bg-surface-darkSecondary text-brand-primary shadow-xs'
                    : 'text-content-secondary hover:text-content-primary'
                }`}
                title="Grid view"
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-1.5 rounded-lg transition-colors ${
                  viewMode === 'list'
                    ? 'bg-white dark:bg-surface-darkSecondary text-brand-primary shadow-xs'
                    : 'text-content-secondary hover:text-content-primary'
                }`}
                title="List view"
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </Card>

      {/* Results Content */}
      {filteredMeetings.length === 0 ? (
        <EmptyState
          icon={<Calendar className="w-8 h-8" />}
          title="No meetings found"
          description={
            search
              ? `No meetings match "${search}". Try adjusting your filters.`
              : 'You have not uploaded any meeting audio recordings yet. Get started by creating your first meeting.'
          }
          actionLabel="New Meeting"
          onAction={() => navigate('/meetings/new')}
        />
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredMeetings.map((m) => {
            const decCount = decisions.filter((d) => d.meetingId === m.id).length;
            const actCount = actionItems.filter((a) => a.meetingId === m.id).length;

            return (
              <Card
                key={m.id}
                hover
                onClick={() => navigate(`/meetings/${m.id}`)}
                className="p-5 flex flex-col justify-between cursor-pointer group"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="text-[11px] font-medium px-2 py-0.5 rounded-md bg-surface-secondary dark:bg-surface-darkSecondary text-content-secondary border border-edge-light dark:border-edge-dark">
                      {m.meetingType}
                    </span>

                    {m.analysisStatus === 'completed' ? (
                      <Badge variant="indigo" size="sm" dot>
                        Analyzed
                      </Badge>
                    ) : (
                      <Badge variant="neutral" size="sm">
                        Ready
                      </Badge>
                    )}
                  </div>

                  <h3 className="text-base font-semibold text-content-primary dark:text-content-darkPrimary group-hover:text-brand-primary transition-colors line-clamp-1">
                    {m.title}
                  </h3>

                  {m.description && (
                    <p className="text-xs text-content-secondary dark:text-content-darkSecondary mt-1.5 line-clamp-2 leading-relaxed">
                      {m.description}
                    </p>
                  )}

                  <div className="mt-4 pt-3 border-t border-edge-light dark:border-edge-dark flex items-center justify-between text-xs text-content-secondary">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      {formatDateTime(m.meetingDate)}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {formatDuration(m.durationSeconds)}
                    </span>
                  </div>

                  {m.participants.length > 0 && (
                    <div className="mt-2 text-xs text-content-secondary flex items-center gap-1.5 truncate">
                      <Users className="w-3.5 h-3.5 shrink-0" />
                      <span className="truncate">{m.participants.join(', ')}</span>
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-edge-light dark:border-edge-dark flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800/60">
                      <CheckCircle2 className="w-3 h-3" />
                      {decCount}
                    </span>
                    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-brand-primary dark:text-brand-secondary bg-brand-light dark:bg-brand-primary/15 px-2 py-0.5 rounded-full border border-brand-primary/20">
                      <ListTodo className="w-3 h-3" />
                      {actCount}
                    </span>
                  </div>

                  <button
                    onClick={(e) => handleDeleteMeeting(e, m.id, m.title)}
                    className="p-1.5 rounded-lg text-content-secondary hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
                    title="Delete meeting"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </Card>
            );
          })}
        </div>
      ) : (
        /* List View */
        <Card className="divide-y divide-edge-light dark:border-edge-dark overflow-hidden">
          {filteredMeetings.map((m) => {
            const decCount = decisions.filter((d) => d.meetingId === m.id).length;
            const actCount = actionItems.filter((a) => a.meetingId === m.id).length;

            return (
              <div
                key={m.id}
                onClick={() => navigate(`/meetings/${m.id}`)}
                className="p-4 sm:p-5 hover:bg-surface-secondary/40 dark:hover:bg-surface-darkSecondary/30 transition-colors cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-surface-secondary dark:bg-surface-darkSecondary text-content-secondary border border-edge-light dark:border-edge-dark">
                      {m.meetingType}
                    </span>
                    {m.analysisStatus === 'completed' && (
                      <Badge variant="indigo" size="sm" dot>
                        Analyzed
                      </Badge>
                    )}
                  </div>
                  <h4 className="text-base font-semibold text-content-primary dark:text-content-darkPrimary group-hover:text-brand-primary transition-colors truncate">
                    {m.title}
                  </h4>
                  <p className="text-xs text-content-secondary mt-0.5 truncate">
                    {m.participants.join(', ') || 'No attendees specified'}
                  </p>
                </div>

                <div className="flex items-center gap-4 self-end sm:self-center shrink-0">
                  <div className="text-right text-xs text-content-secondary">
                    <p>{formatDateTime(m.meetingDate)}</p>
                    <p>{formatDuration(m.durationSeconds)}</p>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-full border border-emerald-200">
                      <CheckCircle2 className="w-3 h-3" />
                      {decCount}
                    </span>
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-brand-primary bg-brand-light px-2 py-0.5 rounded-full border border-brand-primary/20">
                      <ListTodo className="w-3 h-3" />
                      {actCount}
                    </span>
                  </div>

                  <button
                    onClick={(e) => handleDeleteMeeting(e, m.id, m.title)}
                    className="p-1.5 rounded-lg text-content-secondary hover:text-rose-600 hover:bg-rose-50 transition-colors"
                    title="Delete meeting"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </Card>
      )}
    </div>
  );
};
