import React, { useState } from 'react';
import {
  CheckCircle2,
  Clock,
  User,
  Calendar,
  Edit,
  ArrowRight,
  GripVertical,
} from 'lucide-react';
import { ActionItem, TaskStatus } from '../../types';
import { Card } from '../ui/Card';
import { PRIORITY_CONFIG } from '../../config/constants';
import { formatDate } from '../../utils/formatters';
import { useData } from '../../context/DataContext';
import { toast } from 'sonner';

interface ActionItemBoardProps {
  tasks: ActionItem[];
  onEdit: (task: ActionItem) => void;
}

export const ActionItemBoard: React.FC<ActionItemBoardProps> = ({ tasks, onEdit }) => {
  const { updateActionItem } = useData();

  const [draggedTaskId, setDraggedTaskId] = useState<string | null>(null);
  const [dragOverCol, setDragOverCol] = useState<TaskStatus | null>(null);

  const columns: { status: TaskStatus; label: string; dot: string }[] = [
    { status: 'To Do', label: 'To Do', dot: 'bg-slate-400' },
    { status: 'In Progress', label: 'In Progress', dot: 'bg-indigo-500' },
    { status: 'Blocked', label: 'Blocked', dot: 'bg-rose-500' },
    { status: 'Completed', label: 'Completed', dot: 'bg-emerald-500' },
  ];

  const handleDragStart = (e: React.DragEvent, taskId: string) => {
    e.dataTransfer.setData('text/plain', taskId);
    e.dataTransfer.effectAllowed = 'move';
    setDraggedTaskId(taskId);
  };

  const handleDragEnd = () => {
    setDraggedTaskId(null);
    setDragOverCol(null);
  };

  const handleDragOver = (e: React.DragEvent, status: TaskStatus) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (dragOverCol !== status) {
      setDragOverCol(status);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    // Only clear if leaving the column element itself
    if (e.currentTarget.contains(e.relatedTarget as Node)) return;
    setDragOverCol(null);
  };

  const handleDrop = async (e: React.DragEvent, newStatus: TaskStatus) => {
    e.preventDefault();
    setDragOverCol(null);
    const taskId = e.dataTransfer.getData('text/plain') || draggedTaskId;

    if (!taskId) return;

    const task = tasks.find((t) => t.id === taskId);
    if (!task) return;

    if (task.status === newStatus) {
      setDraggedTaskId(null);
      return;
    }

    try {
      await updateActionItem(taskId, { status: newStatus });
      toast.success(`Task "${task.title}" updated to ${newStatus}`);
    } catch (err: any) {
      toast.error(`Failed to update task status: ${err.message}`);
    } finally {
      setDraggedTaskId(null);
    }
  };

  return (
    <div className="space-y-2">
      <div className="text-right text-[11px] text-content-secondary dark:text-content-darkSecondary">
        💡 Tip: Drag and drop cards between status columns to update progress in real time.
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {columns.map((col) => {
          const columnTasks = tasks.filter((t) => t.status === col.status);
          const isDragOver = dragOverCol === col.status;

          return (
            <div
              key={col.status}
              onDragOver={(e) => handleDragOver(e, col.status)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, col.status)}
              className={`flex flex-col rounded-2xl border p-3.5 min-h-[520px] transition-all duration-200 ${
                isDragOver
                  ? 'border-brand-primary bg-brand-light/30 dark:bg-brand-primary/15 ring-2 ring-brand-primary/30 shadow-md'
                  : 'bg-surface-secondary/40 dark:bg-surface-darkSecondary/30 border-edge-light dark:border-edge-dark'
              }`}
            >
              {/* Column Header */}
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-edge-light dark:border-edge-dark">
                <div className="flex items-center gap-2">
                  <span className={`w-2.5 h-2.5 rounded-full ${col.dot}`} />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-content-primary dark:text-content-darkPrimary">
                    {col.label}
                  </h4>
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-white dark:bg-surface-darkSecondary text-content-secondary border border-edge-light dark:border-edge-dark">
                  {columnTasks.length}
                </span>
              </div>

              {/* Task Cards in Column */}
              <div className="space-y-3 flex-1 overflow-y-auto">
                {columnTasks.length === 0 ? (
                  <div
                    className={`py-12 text-center text-xs border border-dashed rounded-xl transition-colors ${
                      isDragOver
                        ? 'border-brand-primary text-brand-primary font-medium bg-brand-light/40 dark:bg-brand-primary/10'
                        : 'border-edge-light dark:border-edge-dark text-content-secondary/60'
                    }`}
                  >
                    {isDragOver ? 'Drop task here' : 'Drop tasks here'}
                  </div>
                ) : (
                  columnTasks.map((task) => {
                    const priorityCfg = PRIORITY_CONFIG[task.priority];
                    const isOverdue =
                      task.dueDate &&
                      task.status !== 'Completed' &&
                      new Date(task.dueDate).getTime() < Date.now();
                    const isBeingDragged = draggedTaskId === task.id;

                    return (
                      <Card
                        key={task.id}
                        draggable
                        onDragStart={(e) => handleDragStart(e, task.id)}
                        onDragEnd={handleDragEnd}
                        hover
                        className={`p-3.5 bg-white dark:bg-surface-darkCard flex flex-col justify-between cursor-grab active:cursor-grabbing select-none transition-all ${
                          isBeingDragged
                            ? 'opacity-40 scale-95 border-dashed border-brand-primary'
                            : 'shadow-xs hover:shadow-md'
                        }`}
                        onClick={() => onEdit(task)}
                      >
                        <div>
                          <div className="flex items-center justify-between gap-1 mb-2">
                            <div className="flex items-center gap-1.5">
                              <GripVertical className="w-3.5 h-3.5 text-content-secondary/40 shrink-0" />
                              <span
                                className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${priorityCfg.bg} ${priorityCfg.text} ${priorityCfg.border}`}
                              >
                                {task.priority}
                              </span>
                            </div>

                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                onEdit(task);
                              }}
                              className="p-1 rounded text-content-secondary hover:text-content-primary transition-colors"
                              title="Edit task"
                            >
                              <Edit className="w-3.5 h-3.5" />
                            </button>
                          </div>

                          <h5 className="text-xs font-semibold text-content-primary dark:text-content-darkPrimary line-clamp-2 leading-snug">
                            {task.title}
                          </h5>

                          {task.description && (
                            <p className="text-[11px] text-content-secondary dark:text-content-darkSecondary mt-1 line-clamp-2 leading-relaxed">
                              {task.description}
                            </p>
                          )}
                        </div>

                        <div className="mt-3 pt-2.5 border-t border-edge-light dark:border-edge-dark flex items-center justify-between text-[11px] text-content-secondary dark:text-content-darkSecondary">
                          <span className="flex items-center gap-1 font-medium text-content-primary dark:text-content-darkPrimary truncate max-w-[100px]">
                            <User className="w-3 h-3 text-content-secondary shrink-0" />
                            {task.assignee || 'Unassigned'}
                          </span>

                          <span
                            className={`truncate ${
                              isOverdue ? 'text-rose-600 dark:text-rose-400 font-semibold' : ''
                            }`}
                          >
                            {task.dueDate ? formatDate(task.dueDate) : 'No date'}
                          </span>
                        </div>
                      </Card>
                    );
                  })
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
