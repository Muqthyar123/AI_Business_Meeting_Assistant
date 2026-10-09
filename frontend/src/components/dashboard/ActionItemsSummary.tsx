import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ListTodo, CheckCircle2, AlertCircle, ChevronRight, User } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { PRIORITY_CONFIG, TASK_STATUS_CONFIG } from '../../config/constants';
import { formatDate } from '../../utils/formatters';
import { useData } from '../../context/DataContext';

export const ActionItemsSummary: React.FC = () => {
  const navigate = useNavigate();
  const { actionItems, updateActionItem } = useData();

  const openTasks = actionItems
    .filter((a) => a.status !== 'Completed' && a.status !== 'Cancelled')
    .slice(0, 4);

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Action Items Due</CardTitle>
          <CardDescription>Priority tasks requiring immediate follow-through</CardDescription>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/action-items')}
          rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
        >
          View Board
        </Button>
      </CardHeader>

      <CardContent className="p-0">
        <div className="divide-y divide-edge-light dark:divide-edge-dark">
          {openTasks.length === 0 ? (
            <div className="p-6 text-center text-xs text-content-secondary dark:text-content-darkSecondary">
              All caught up! No open action items pending.
            </div>
          ) : (
            openTasks.map((task) => {
              const priorityCfg = PRIORITY_CONFIG[task.priority];
              const isOverdue =
                task.dueDate && new Date(task.dueDate).getTime() < Date.now();

              return (
                <div
                  key={task.id}
                  className="p-4 hover:bg-surface-secondary/40 dark:hover:bg-surface-darkSecondary/30 transition-colors flex items-start justify-between gap-3 group"
                >
                  <div className="flex items-start gap-3 min-w-0">
                    <button
                      onClick={() =>
                        updateActionItem(task.id, {
                          status: task.status === 'Completed' ? 'To Do' : 'Completed',
                        })
                      }
                      className="mt-0.5 text-content-secondary hover:text-emerald-600 transition-colors shrink-0"
                      title="Mark complete"
                    >
                      <CheckCircle2
                        className={`w-4 h-4 ${
                          task.status === 'Completed'
                            ? 'text-emerald-500 fill-emerald-500/20'
                            : 'opacity-50 hover:opacity-100'
                        }`}
                      />
                    </button>

                    <div className="min-w-0">
                      <p className="text-sm font-medium text-content-primary dark:text-content-darkPrimary truncate">
                        {task.title}
                      </p>
                      <div className="flex flex-wrap items-center gap-2 mt-1 text-[11px] text-content-secondary dark:text-content-darkSecondary">
                        <span className="flex items-center gap-1 font-medium text-content-primary dark:text-content-darkPrimary">
                          <User className="w-3 h-3 text-content-secondary" />
                          {task.assignee || 'Unassigned'}
                        </span>
                        <span>•</span>
                        <span className={isOverdue ? 'text-rose-600 font-semibold' : ''}>
                          Due: {task.dueDate ? formatDate(task.dueDate) : 'No deadline'}
                        </span>
                        {task.meetingTitle && (
                          <>
                            <span>•</span>
                            <span className="truncate max-w-[150px]">
                              {task.meetingTitle}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${priorityCfg.bg} ${priorityCfg.text} ${priorityCfg.border}`}
                    >
                      {task.priority}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </CardContent>
    </Card>
  );
};
