import React, { useState, useMemo } from 'react';
import {
  CheckCircle2,
  Plus,
  Search,
  Download,
  Filter,
  Calendar,
  Layers,
  ArrowUpDown,
} from 'lucide-react';
import { Decision, DecisionStatus } from '../types';
import { DecisionCard } from '../components/decisions/DecisionCard';
import { DecisionFormModal } from '../components/decisions/DecisionFormModal';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { exportDecisionsCsv } from '../utils/exportHelpers';
import { useData } from '../context/DataContext';
import { toast } from 'sonner';

export const DecisionsPage: React.FC = () => {
  const { decisions, meetings } = useData();

  const [search, setSearch] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedMeetingId, setSelectedMeetingId] = useState<string>('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingDecision, setEditingDecision] = useState<Decision | null>(null);

  const filteredDecisions = useMemo(() => {
    return decisions.filter((d) => {
      const matchesSearch =
        d.title.toLowerCase().includes(search.toLowerCase()) ||
        d.description.toLowerCase().includes(search.toLowerCase()) ||
        (d.owner && d.owner.toLowerCase().includes(search.toLowerCase())) ||
        (d.evidence && d.evidence.toLowerCase().includes(search.toLowerCase()));

      const matchesStatus =
        selectedStatus === 'all' || d.status === selectedStatus;

      const matchesMeeting =
        selectedMeetingId === 'all' || d.meetingId === selectedMeetingId;

      return matchesSearch && matchesStatus && matchesMeeting;
    });
  }, [decisions, search, selectedStatus, selectedMeetingId]);

  const handleExportCsv = () => {
    exportDecisionsCsv(filteredDecisions, 'meetmind_decisions.csv');
    toast.success('Decisions exported to CSV');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-content-primary dark:text-content-darkPrimary flex items-center gap-2.5">
            <CheckCircle2 className="w-6 h-6 text-emerald-500" />
            Decisions Management
          </h1>
          <p className="text-xs sm:text-sm text-content-secondary dark:text-content-darkSecondary mt-0.5">
            Explicit executive commitments and organizational agreements extracted from meetings
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportCsv}
            leftIcon={<Download className="w-3.5 h-3.5" />}
          >
            Export CSV
          </Button>

          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="w-3.5 h-3.5" />}
            onClick={() => {
              setEditingDecision(null);
              setIsModalOpen(true);
            }}
          >
            Record Decision
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <Card className="p-4">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-content-secondary absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search decisions by title, keyword, or owner..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-xl border border-edge-light dark:border-edge-dark bg-surface-secondary/40 text-xs sm:text-sm text-content-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2 w-full lg:w-auto">
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="text-xs px-3 py-2 rounded-xl border border-edge-light dark:border-edge-dark bg-white dark:bg-surface-darkSecondary text-content-primary focus:outline-none"
            >
              <option value="all">All Statuses</option>
              <option value="Confirmed">Confirmed</option>
              <option value="Proposed">Proposed</option>
              <option value="Rejected">Rejected</option>
              <option value="Superseded">Superseded</option>
            </select>

            <select
              value={selectedMeetingId}
              onChange={(e) => setSelectedMeetingId(e.target.value)}
              className="text-xs px-3 py-2 rounded-xl border border-edge-light dark:border-edge-dark bg-white dark:bg-surface-darkSecondary text-content-primary focus:outline-none max-w-[200px] truncate"
            >
              <option value="all">All Source Meetings</option>
              {meetings.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.title}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Grid of Decisions */}
      {filteredDecisions.length === 0 ? (
        <EmptyState
          icon={<CheckCircle2 className="w-8 h-8 text-emerald-500" />}
          title="No decisions found"
          description={
            search
              ? `No decisions match "${search}". Try adjusting your filters.`
              : 'No decisions have been captured yet. Record a decision manually or analyze a meeting.'
          }
          actionLabel="Record Decision"
          onAction={() => {
            setEditingDecision(null);
            setIsModalOpen(true);
          }}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDecisions.map((decision) => (
            <DecisionCard
              key={decision.id}
              decision={decision}
              onEdit={(d) => {
                setEditingDecision(d);
                setIsModalOpen(true);
              }}
            />
          ))}
        </div>
      )}

      {/* Create / Edit Modal */}
      <DecisionFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        decision={editingDecision}
      />
    </div>
  );
};
