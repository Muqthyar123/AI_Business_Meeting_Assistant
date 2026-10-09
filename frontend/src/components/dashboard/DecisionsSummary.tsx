import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, ChevronRight, Quote } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { DECISION_STATUS_CONFIG } from '../../config/constants';
import { truncateText } from '../../utils/formatters';
import { Button } from '../ui/Button';
import { useData } from '../../context/DataContext';

export const DecisionsSummary: React.FC = () => {
  const navigate = useNavigate();
  const { decisions } = useData();

  const recentDecisions = [...decisions].slice(0, 4);

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Decisions Captured</CardTitle>
          <CardDescription>Explicit leadership commitments extracted from meetings</CardDescription>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/decisions')}
          rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
        >
          View All
        </Button>
      </CardHeader>

      <CardContent className="p-0">
        <div className="divide-y divide-edge-light dark:divide-edge-dark">
          {recentDecisions.length === 0 ? (
            <div className="p-6 text-center text-xs text-content-secondary dark:text-content-darkSecondary">
              No decisions recorded yet.
            </div>
          ) : (
            recentDecisions.map((decision) => {
              const statusCfg = DECISION_STATUS_CONFIG[decision.status] || {
                bg: 'bg-slate-100',
                text: 'text-slate-700',
                border: 'border-slate-200',
              };

              return (
                <div
                  key={decision.id}
                  onClick={() => navigate('/decisions')}
                  className="p-4 hover:bg-surface-secondary/40 dark:hover:bg-surface-darkSecondary/30 transition-colors cursor-pointer group"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                        <h4 className="text-sm font-semibold text-content-primary dark:text-content-darkPrimary group-hover:text-brand-primary transition-colors truncate">
                          {decision.title}
                        </h4>
                      </div>
                      <p className="text-xs text-content-secondary dark:text-content-darkSecondary mt-1 line-clamp-2">
                        {decision.description}
                      </p>

                      {decision.evidence && (
                        <div className="mt-2 text-[11px] text-content-secondary/80 italic flex items-start gap-1 bg-surface-secondary/50 dark:bg-surface-darkSecondary/40 p-2 rounded-lg border border-edge-light dark:border-edge-dark">
                          <Quote className="w-3 h-3 text-brand-primary shrink-0 mt-0.5 not-italic" />
                          <span className="line-clamp-1">&ldquo;{decision.evidence}&rdquo;</span>
                        </div>
                      )}
                    </div>

                    <div className="shrink-0 flex flex-col items-end gap-1">
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${statusCfg.bg} ${statusCfg.text} ${statusCfg.border}`}
                      >
                        {decision.status}
                      </span>
                      {decision.owner && (
                        <span className="text-[11px] text-content-secondary truncate max-w-[100px]">
                          {decision.owner}
                        </span>
                      )}
                    </div>
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
