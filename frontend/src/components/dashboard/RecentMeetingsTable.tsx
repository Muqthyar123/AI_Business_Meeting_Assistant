import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, Clock, ChevronRight, Sparkles, CheckCircle2, ListTodo, FileText } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { formatDateTime, formatDuration } from '../../utils/formatters';
import { useData } from '../../context/DataContext';

export const RecentMeetingsTable: React.FC = () => {
  const navigate = useNavigate();
  const { meetings, decisions, actionItems } = useData();

  const recentMeetings = [...meetings]
    .sort((a, b) => new Date(b.meetingDate).getTime() - new Date(a.meetingDate).getTime())
    .slice(0, 5);

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <div>
          <CardTitle>Recent Meetings</CardTitle>
          <CardDescription>Latest executive sessions and processed recordings</CardDescription>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/meetings')}
          rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
        >
          View All
        </Button>
      </CardHeader>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-edge-light dark:border-edge-dark bg-surface-secondary/40 dark:bg-surface-darkSecondary/30 text-[11px] font-semibold uppercase tracking-wider text-content-secondary dark:text-content-darkSecondary">
              <th className="py-3 px-4 sm:px-6">Meeting</th>
              <th className="py-3 px-3">Date & Time</th>
              <th className="py-3 px-3">Duration</th>
              <th className="py-3 px-3">AI Insights</th>
              <th className="py-3 px-3 text-center">Decisions</th>
              <th className="py-3 px-3 text-center">Action Items</th>
              <th className="py-3 px-4 sm:px-6 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-edge-light dark:divide-edge-dark text-sm">
            {recentMeetings.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-xs text-content-secondary">
                  No meetings recorded yet. Click &ldquo;New Meeting&rdquo; to upload an audio file.
                </td>
              </tr>
            ) : (
              recentMeetings.map((m) => {
                const decCount = decisions.filter((d) => d.meetingId === m.id).length;
                const actCount = actionItems.filter((a) => a.meetingId === m.id).length;

                return (
                  <tr
                    key={m.id}
                    onClick={() => navigate(`/meetings/${m.id}`)}
                    className="hover:bg-surface-secondary/50 dark:hover:bg-surface-darkSecondary/40 cursor-pointer transition-colors group"
                  >
                    <td className="py-3.5 px-4 sm:px-6">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-brand-light dark:bg-brand-primary/10 text-brand-primary dark:text-brand-secondary flex items-center justify-center shrink-0">
                          <Calendar className="w-4 h-4" />
                        </div>
                        <div className="min-w-0">
                          <p className="font-semibold text-content-primary dark:text-content-darkPrimary group-hover:text-brand-primary transition-colors truncate max-w-[200px] sm:max-w-[280px]">
                            {m.title}
                          </p>
                          <span className="text-[11px] text-content-secondary dark:text-content-darkSecondary">
                            {m.meetingType} • {m.department || 'General'}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-3 text-xs text-content-secondary dark:text-content-darkSecondary whitespace-nowrap">
                      {formatDateTime(m.meetingDate)}
                    </td>

                    <td className="py-3.5 px-3 text-xs text-content-secondary dark:text-content-darkSecondary whitespace-nowrap">
                      <span className="inline-flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 opacity-70" />
                        {formatDuration(m.durationSeconds)}
                      </span>
                    </td>

                    <td className="py-3.5 px-3 whitespace-nowrap">
                      {m.analysisStatus === 'completed' ? (
                        <Badge variant="indigo" size="sm" dot>
                          Analyzed
                        </Badge>
                      ) : m.analysisStatus === 'pending' ? (
                        <Badge variant="warning" size="sm" dot>
                          Analyzing...
                        </Badge>
                      ) : (
                        <Badge variant="neutral" size="sm">
                          Ready
                        </Badge>
                      )}
                    </td>

                    <td className="py-3.5 px-3 text-center whitespace-nowrap">
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800/60">
                        <CheckCircle2 className="w-3 h-3" />
                        {decCount}
                      </span>
                    </td>

                    <td className="py-3.5 px-3 text-center whitespace-nowrap">
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-brand-primary dark:text-brand-secondary bg-brand-light dark:bg-brand-primary/15 px-2 py-0.5 rounded-full border border-brand-primary/20">
                        <ListTodo className="w-3 h-3" />
                        {actCount}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 sm:px-6 text-right whitespace-nowrap">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-xs h-7 px-2.5 opacity-80 group-hover:opacity-100"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/meetings/${m.id}`);
                        }}
                      >
                        Details
                      </Button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
};
