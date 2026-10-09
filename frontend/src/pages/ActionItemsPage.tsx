import React, { useState, useMemo } from 'react';
import {
  ListTodo,
  Plus,
  Search,
  Download,
  Filter,
  LayoutGrid,
  List,
  AlertTriangle,
  User,
  CheckCircle2,
} from 'lucide-react';
import { ActionItem, PriorityLevel, TaskStatus } from '../types';
import { ActionItemList } from '../components/action-items/ActionItemList';
import { ActionItemBoard } from '../components/action-items/ActionItemBoard';
import { ActionItemFormModal } from '../components/action-items/ActionItemFormModal';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { exportActionItemsCsv } from '../utils/exportHelpers';
import { useData } from '../context/DataContext';
import { toast } from 'sonner';

export const ActionItemsPage: React.FC = () => {
  const { actionItems, meetings } = useData();

  const [search, setSearch] = useState('');
  const [activeFilterTab, setActiveFilterTab] = useState<
    'all' | 'todo' | 'in-progress' | 'blocked' | 'completed' | 'overdue'
  >('all');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');
  const [selectedMeetingId, setSelectedMeetingId] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'list' | 'board'>('board');

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<ActionItem | null>(null);

  const filteredTasks = useMemo(() => {
    const now = Date.now();

    return actionItems.filter((t) => {
      const matchesSearch =
        t.title.toLowerCase().includes(search.toLowerCase()) ||
        (t.description && t.description.toLowerCase().includes(search.toLowerCase())) ||
        (t.assignee && t.assignee.toLowerCase().includes(search.toLowerCase())) ||
        (t.evidence && t.evidence.toLowerCase().includes(search.toLowerCase()));

      let matchesTab = true;
      if (activeFilterTab === 'todo') matchesTab = t.status === 'To Do';
      else if (activeFilterTab === 'in-progress') matchesTab = t.status === 'In Progress';
      else if (activeFilterTab === 'blocked') matchesTab = t.status === 'Blocked';
      else if (activeFilterTab === 'completed') matchesTab = t.status === 'Completed';
      else if (activeFilterTab === 'overdue') {
        matchesTab =
          t.status !== 'Completed' &&
          t.status !== 'Cancelled' &&
          Boolean(t.dueDate && new Date(t.dueDate).getTime() < now);
      }

      const matchesPriority =
        selectedPriority === 'all' || t.priority === selectedPriority;

      const matchesMeeting =
        selectedMeetingId === 'all' || t.meetingId === selectedMeetingId;

      return matchesSearch && matchesTab && matchesPriority && matchesMeeting;
    });
  }, [actionItems, search, activeFilterTab, selectedPriority, selectedMeetingId]);

  const handleExportCsv = () => {
    exportActionItemsCsv(filteredTasks, 'meetmind_action_items.csv');
    toast.success('Action items exported to CSV');
  };

  const overdueCount = useMemo(() => {
    const now = Date.now();
    return actionItems.filter(
      (t) =>
        t.status !== 'Completed' &&
        t.status !== 'Cancelled' &&
        Boolean(t.dueDate && new Date(t.dueDate).getTime() < now)
    ).length;
  }, [actionItems]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-content-primary dark:text-content-darkPrimary flex items-center gap-2.5">
            <ListTodo className="w-6 h-6 text-brand-secondary" />
            Action Items & Task Execution
          </h1>
          <p className="text-xs sm:text-sm text-content-secondary dark:text-content-darkSecondary mt-0.5">
            Track assignees, deadlines, and deliverables extracted from meeting audio
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
              setEditingTask(null);
              setIsModalOpen(true);
            }}
          >
            New Task
          </Button>
        </div>
      </div>

      {/* Filter Tabs Bar */}
      <div className="flex items-center justify-between gap-2 overflow-x-auto border-b border-edge-light dark:border-edge-dark pb-1 no-scrollbar">
        <div className="flex items-center gap-1">
          {[
            { id: 'all', label: 'All Tasks', count: actionItems.length },
            {
              id: 'todo',
              label: 'To Do',
              count: actionItems.filter((a) => a.status === 'To Do').length,
            },
            {
              id: 'in-progress',
              label: 'In Progress',
              count: actionItems.filter((a) => a.status === 'In Progress').length,
            },
            {
              id: 'blocked',
              label: 'Blocked',
              count: actionItems.filter((a) => a.status === 'Blocked').length,
            },
            {
              id: 'completed',
              label: 'Completed',
              count: actionItems.filter((a) => a.status === 'Completed').length,
            },
            { id: 'overdue', label: 'Overdue', count: overdueCount },
          ].map((tab) => {
            const isActive = activeFilterTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveFilterTab(tab.id as any)}
                className={`px-3 py-2 text-xs font-semibold rounded-xl transition-all whitespace-nowrap flex items-center gap-1.5 ${
                  isActive
                    ? 'bg-brand-primary text-white shadow-xs'
                    : 'text-content-secondary hover:text-content-primary hover:bg-surface-secondary'
                }`}
              >
                <span>{tab.label}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                    isActive
                      ? 'bg-white/20 text-white'
                      : 'bg-surface-secondary dark:bg-surface-darkSecondary text-content-secondary'
                  }`}
                >
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* View toggle */}
        <div className="flex rounded-xl border border-edge-light dark:border-edge-dark p-0.5 bg-surface-secondary/40 shrink-0">
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
          <button
            onClick={() => setViewMode('board')}
            className={`p-1.5 rounded-lg transition-colors ${
              viewMode === 'board'
                ? 'bg-white dark:bg-surface-darkSecondary text-brand-primary shadow-xs'
                : 'text-content-secondary hover:text-content-primary'
            }`}
            title="Board view"
          >
            <LayoutGrid className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <Card className="p-4">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-content-secondary absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search action items by title, assignee, or description..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-xl border border-edge-light dark:border-edge-dark bg-surface-secondary/40 text-xs sm:text-sm text-content-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2 w-full lg:w-auto">
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="text-xs px-3 py-2 rounded-xl border border-edge-light dark:border-edge-dark bg-white dark:bg-surface-darkSecondary text-content-primary focus:outline-none"
            >
              <option value="all">All Priorities</option>
              <option value="Urgent">Urgent</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>

            <select
              value={selectedMeetingId}
              onChange={(e) => setSelectedMeetingId(e.target.value)}
              className="text-xs px-3 py-2 rounded-xl border border-edge-light dark:border-edge-dark bg-white dark:bg-surface-darkSecondary text-content-primary focus:outline-none max-w-[200px] truncate"
            >
              <option value="all">All Meetings</option>
              {meetings.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.title}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Views */}
      {filteredTasks.length === 0 ? (
        <EmptyState
          icon={<ListTodo className="w-8 h-8 text-brand-secondary" />}
          title="No action items found"
          description={
            search
              ? `No tasks match "${search}". Try adjusting your filters.`
              : 'You have no active action items. Create a new task manually or analyze a meeting.'
          }
          actionLabel="Create Task"
          onAction={() => {
            setEditingTask(null);
            setIsModalOpen(true);
          }}
        />
      ) : viewMode === 'list' ? (
        <ActionItemList
          tasks={filteredTasks}
          onEdit={(task) => {
            setEditingTask(task);
            setIsModalOpen(true);
          }}
        />
      ) : (
        <ActionItemBoard
          tasks={filteredTasks}
          onEdit={(task) => {
            setEditingTask(task);
            setIsModalOpen(true);
          }}
        />
      )}

      {/* Task Form Modal */}
      <ActionItemFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        task={editingTask}
      />
    </div>
  );
};
