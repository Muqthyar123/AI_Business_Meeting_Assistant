import React from 'react';
import { Link } from 'react-router-dom';
import {
  CheckCircle2,
  Clock,
  User,
  Calendar,
  MoreHorizontal,
  Edit,
  Trash2,
  ExternalLink,
  Quote,
} from 'lucide-react';
import { ActionItem, TaskStatus } from '../../types';
import { Card } from '../ui/Card';
import { PRIORITY_CONFIG, TASK_STATUS_CONFIG } from '../../config/constants';
import { formatDate } from '../../utils/formatters';
import { useData } from '../../context/DataContext';

interface ActionItemListProps {
  tasks: ActionItem[];
  onEdit: (task: ActionItem) => void;
}

export const ActionItemList: React.FC<ActionItemListProps> = ({ tasks, onEdit }) => {
  const { updateActionItem, deleteActionItem } = useData();

  const handleToggleComplete = (task: ActionItem) => {
    updateActionItem(task.id, {
      status: task.status === 'Completed' ? 'To Do' : 'Completed',
    });
  };

  const handleStatusChange = (task: ActionItem, newStatus: TaskStatus) => {
    updateActionItem(task.id, { status: newStatus });
  };

  const handleDelete = (task: ActionItem) => {
    if (window.confirm(`Delete task "${task.title}"?`)) {
      deleteActionItem(task.id);
    }
  };

  return (
    <Card className="divide-y divide-edge-light dark:divide-edge-dark overflow-hidden">
      {tasks.length === 0 ? (
        <div className="p-8 text-center text-xs text-content-secondary dark:text-content-darkSecondary">
          No action items found for the selected criteria.
        </div>
      ) : (
        tasks.map((task) => {
          const priorityCfg = PRIORITY_CONFIG[task.priority];
          const statusCfg = TASK_STATUS_CONFIG[task.status] || {
            label: task.status,
            bg: 'bg-slate-100',
            text: 'text-slate-700',
            dot: 'bg-slate-400',
          };
          const isOverdue =
            task.dueDate &&
            task.status !== 'Completed' &&
            new Date(task.dueDate).getTime() < Date.now();

          return (
            <div
              key={task.id}
              className="p-4 sm:p-5 hover:bg-surface-secondary/40 dark:hover:bg-surface-darkSecondary/30 transition-colors flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 group"
            >
              {/* Left: Checkbox + Title + Meta */}
              <div className="flex items-start gap-3.5 min-w-0 flex-1">
                <button
                  type="button"
                  onClick={() => handleToggleComplete(task)}
                  className="mt-1 text-content-secondary hover:text-emerald-600 transition-colors shrink-0"
                  title={task.status === 'Completed' ? 'Mark incomplete' : 'Mark completed'}
                >
                  <CheckCircle2
                    className={`w-5 h-5 ${
                      task.status === 'Completed'
                        ? 'text-emerald-500 fill-emerald-500/20'
                        : 'opacity-40 hover:opacity-100'
                    }`}
                  />
                </button>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h4
                      className={`text-sm sm:text-base font-semibold text-content-primary dark:text-content-darkPrimary tracking-tight ${
                        task.status === 'Completed' ? 'line-through opacity-60' : ''
                      }`}
                    >
                      {task.title}
                    </h4>

                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${priorityCfg.bg} ${priorityCfg.text} ${priorityCfg.border}`}
                    >
                      {task.priority}
                    </span>

                    {task.isManual && (
                      <span className="text-[10px] text-content-secondary bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">
                        Manual
                      </span>
                    )}
                  </div>

                  {task.description && (
                    <p className="text-xs text-content-secondary dark:text-content-darkSecondary mt-1 leading-relaxed">
                      {task.description}
                    </p>
                  )}

                  {task.evidence && (
                    <div className="mt-2 text-[11px] text-content-secondary/80 italic flex items-center gap-1.5">
                      <Quote className="w-3 h-3 text-brand-primary shrink-0 not-italic" />
                      <span className="truncate max-w-xl">&ldquo;{task.evidence}&rdquo;</span>
                    </div>
                  )}

                  <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-content-secondary dark:text-content-darkSecondary">
                    <span className="flex items-center gap-1 font-medium text-content-primary dark:text-content-darkPrimary">
                      <User className="w-3.5 h-3.5 text-content-secondary" />
                      {task.assignee || 'Unassigned'}
                    </span>

                    <span>•</span>

                    <span
                      className={`flex items-center gap-1 ${
                        isOverdue ? 'text-rose-600 dark:text-rose-400 font-semibold' : ''
                      }`}
                    >
                      <Calendar className="w-3.5 h-3.5" />
                      {task.dueDate ? formatDate(task.dueDate) : 'No deadline'}
                      {isOverdue && ' (Overdue)'}
                    </span>

                    {task.meetingId && task.meetingId !== 'general' && (
                      <>
                        <span>•</span>
                        <Link
                          to={`/meetings/${task.meetingId}`}
                          className="hover:text-brand-primary transition-colors flex items-center gap-1 truncate max-w-[180px]"
                        >
                          <span>{task.meetingTitle || 'View Meeting'}</span>
                          <ExternalLink className="w-3 h-3 shrink-0" />
                        </Link>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Right: Status Selector & Actions */}
              <div className="flex items-center gap-2.5 self-end sm:self-center shrink-0">
                <select
                  value={task.status}
                  onChange={(e) => handleStatusChange(task, e.target.value as TaskStatus)}
                  className={`text-xs font-semibold px-2.5 py-1 rounded-lg border focus:outline-none transition-colors ${statusCfg.bg} ${statusCfg.text} border-edge-light dark:border-edge-dark cursor-pointer`}
                >
                  <option value="To Do">To Do</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Blocked">Blocked</option>
                  <option value="Completed">Completed</option>
                  <option value="Cancelled">Cancelled</option>
                </select>

                <button
                  onClick={() => onEdit(task)}
                  className="p-1.5 rounded-lg text-content-secondary hover:text-content-primary hover:bg-surface-secondary dark:hover:bg-surface-darkSecondary transition-colors"
                  title="Edit task"
                >
                  <Edit className="w-4 h-4" />
                </button>

                <button
                  onClick={() => handleDelete(task)}
                  className="p-1.5 rounded-lg text-content-secondary hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
                  title="Delete task"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })
      )}
    </Card>
  );
};
