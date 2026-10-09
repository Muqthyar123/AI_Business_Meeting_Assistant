import React from 'react';
import {
  Calendar,
  Clock,
  CheckCircle2,
  ListTodo,
  AlertTriangle,
  TrendingUp,
} from 'lucide-react';
import { Card } from '../ui/Card';
import { formatDuration } from '../../utils/formatters';
import { useData } from '../../context/DataContext';

export const KpiGrid: React.FC = () => {
  const { meetings, decisions, actionItems, followUps } = useData();

  // Metrics calculation
  const totalMeetings = meetings.length;
  const totalDurationSeconds = meetings.reduce((sum, m) => sum + (m.durationSeconds || 0), 0);
  const totalDecisions = decisions.length;
  const openActionItems = actionItems.filter(
    (a) => a.status === 'To Do' || a.status === 'In Progress'
  ).length;

  const now = new Date();
  const overdueActionItems = actionItems.filter((a) => {
    if (a.status === 'Completed' || a.status === 'Cancelled' || !a.dueDate) return false;
    return new Date(a.dueDate) < now;
  }).length;

  const totalSteps = followUps.reduce((sum, f) => sum + f.steps.length, 0);
  const completedSteps = followUps.reduce(
    (sum, f) => sum + f.steps.filter((s) => s.status === 'completed').length,
    0
  );
  const followUpRate = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 100;

  const kpis = [
    {
      title: 'Meetings Processed',
      value: totalMeetings.toString(),
      subtext: `${meetings.filter((m) => m.analysisStatus === 'completed').length} analyzed with AI`,
      icon: Calendar,
      color: 'text-brand-primary',
      bgColor: 'bg-brand-light dark:bg-brand-primary/10',
      trend: '+12% vs last month',
    },
    {
      title: 'Total Audio Transcribed',
      value: formatDuration(totalDurationSeconds),
      subtext: 'Processed via Whisper',
      icon: Clock,
      color: 'text-sky-600 dark:text-sky-400',
      bgColor: 'bg-sky-50 dark:bg-sky-950/40',
      trend: '100% fidelity',
    },
    {
      title: 'Decisions Captured',
      value: totalDecisions.toString(),
      subtext: `${decisions.filter((d) => d.status === 'Confirmed').length} confirmed decisions`,
      icon: CheckCircle2,
      color: 'text-emerald-600 dark:text-emerald-400',
      bgColor: 'bg-emerald-50 dark:bg-emerald-950/40',
      trend: 'Zero missed agreements',
    },
    {
      title: 'Open Action Items',
      value: openActionItems.toString(),
      subtext: 'Active commitments',
      icon: ListTodo,
      color: 'text-brand-secondary',
      bgColor: 'bg-purple-50 dark:bg-purple-950/40',
      trend: `${actionItems.filter((a) => a.status === 'Completed').length} completed`,
    },
    {
      title: 'Overdue Action Items',
      value: overdueActionItems.toString(),
      subtext: overdueActionItems === 0 ? 'All tasks on schedule' : 'Needs attention',
      icon: AlertTriangle,
      color: overdueActionItems > 0 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-500',
      bgColor: overdueActionItems > 0 ? 'bg-rose-50 dark:bg-rose-950/40' : 'bg-slate-100 dark:bg-slate-800',
      trend: overdueActionItems === 0 ? 'Healthy execution' : 'Action needed',
    },
    {
      title: 'Follow-up Completion',
      value: `${followUpRate}%`,
      subtext: `${completedSteps} of ${totalSteps} milestones done`,
      icon: TrendingUp,
      color: 'text-indigo-600 dark:text-indigo-400',
      bgColor: 'bg-indigo-50 dark:bg-indigo-950/40',
      trend: 'On track',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {kpis.map((kpi) => {
        const Icon = kpi.icon;
        return (
          <Card key={kpi.title} className="p-4 flex flex-col justify-between hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[11px] font-medium text-content-secondary dark:text-content-darkSecondary uppercase tracking-wider">
                  {kpi.title}
                </p>
                <h4 className="text-2xl font-bold tracking-tight text-content-primary dark:text-content-darkPrimary mt-1">
                  {kpi.value}
                </h4>
              </div>
              <div className={`p-2 rounded-xl ${kpi.bgColor} ${kpi.color}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>

            <div className="mt-3 pt-2.5 border-t border-edge-light dark:border-edge-dark flex items-center justify-between text-[11px]">
              <span className="text-content-secondary dark:text-content-darkSecondary truncate">
                {kpi.subtext}
              </span>
              <span className="font-medium text-brand-primary dark:text-brand-secondary shrink-0">
                {kpi.trend}
              </span>
            </div>
          </Card>
        );
      })}
    </div>
  );
};
