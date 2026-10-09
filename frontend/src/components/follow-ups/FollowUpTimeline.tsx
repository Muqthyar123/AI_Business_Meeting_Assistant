import React from 'react';
import { Link } from 'react-router-dom';
import {
  Milestone,
  CheckCircle2,
  Calendar,
  User,
  ArrowRight,
  Clock,
  ExternalLink,
  Edit,
  Trash2,
} from 'lucide-react';
import { FollowUpPlan, FollowUpStep } from '../../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { useData } from '../../context/DataContext';

interface FollowUpTimelineProps {
  plan: FollowUpPlan;
  onEdit: (plan: FollowUpPlan) => void;
}

export const FollowUpTimeline: React.FC<FollowUpTimelineProps> = ({ plan, onEdit }) => {
  const { saveFollowUp, deleteFollowUp } = useData();

  const totalSteps = plan.steps.length;
  const completedSteps = plan.steps.filter((s) => s.status === 'completed').length;
  const percentComplete = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;

  const toggleStep = (stepId: string) => {
    const updatedSteps = plan.steps.map((s) => {
      if (s.id === stepId) {
        return {
          ...s,
          status: (s.status === 'completed' ? 'pending' : 'completed') as 'pending' | 'completed',
        };
      }
      return s;
    });

    saveFollowUp({
      ...plan,
      steps: updatedSteps,
    });
  };

  const handleDelete = () => {
    if (window.confirm(`Delete follow-up plan: "${plan.title}"?`)) {
      deleteFollowUp(plan.id);
    }
  };

  return (
    <Card className="overflow-hidden">
      {/* Header with Title & Progress */}
      <CardHeader>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                plan.status === 'Active'
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-slate-100 text-slate-700 border-slate-200'
              }`}
            >
              {plan.status}
            </span>
            {plan.meetingTitle && (
              <span className="text-xs text-content-secondary">
                Related: {plan.meetingTitle}
              </span>
            )}
          </div>
          <CardTitle className="text-lg">{plan.title}</CardTitle>
          <CardDescription>{plan.objective}</CardDescription>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => onEdit(plan)} leftIcon={<Edit className="w-3.5 h-3.5" />}>
            Edit Plan
          </Button>
          <button
            onClick={handleDelete}
            className="p-2 rounded-lg text-content-secondary hover:text-rose-600 hover:bg-rose-50 transition-colors"
            title="Delete plan"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Progress Bar */}
        <div className="p-4 rounded-xl bg-surface-secondary/40 dark:bg-surface-darkSecondary/30 border border-edge-light dark:border-edge-dark space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-content-primary dark:text-content-darkPrimary">
              Execution Progress ({completedSteps} of {totalSteps} milestones reached)
            </span>
            <span className="text-brand-primary font-bold">{percentComplete}%</span>
          </div>
          <div className="w-full bg-slate-200 dark:bg-slate-700 h-2.5 rounded-full overflow-hidden">
            <div
              className="bg-brand-primary h-full transition-all duration-300"
              style={{ width: `${percentComplete}%` }}
            />
          </div>
        </div>

        {/* Key Outcomes */}
        {plan.keyOutcomes && plan.keyOutcomes.length > 0 && (
          <div>
            <h5 className="text-xs font-bold uppercase tracking-wider text-content-secondary dark:text-content-darkSecondary mb-2">
              Target Outcomes
            </h5>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {plan.keyOutcomes.map((outcome, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2 p-2.5 rounded-xl bg-brand-light/30 dark:bg-brand-primary/10 border border-brand-primary/20 text-xs text-content-primary dark:text-content-darkPrimary"
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-primary shrink-0 mt-0.5" />
                  <span>{outcome}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Milestone Steps Timeline */}
        <div>
          <h5 className="text-xs font-bold uppercase tracking-wider text-content-secondary dark:text-content-darkSecondary mb-3">
            Milestone Sequence
          </h5>

          <div className="space-y-3 relative before:absolute before:left-4 before:top-4 before:bottom-4 before:w-0.5 before:bg-edge-light dark:before:bg-edge-dark">
            {plan.steps.map((step) => {
              const isDone = step.status === 'completed';

              return (
                <div
                  key={step.id}
                  className="relative flex items-start gap-4 pl-1 group"
                >
                  {/* Step Indicator */}
                  <button
                    onClick={() => toggleStep(step.id)}
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 z-10 transition-colors ${
                      isDone
                        ? 'bg-emerald-500 text-white shadow-sm'
                        : 'bg-white dark:bg-surface-darkCard border-2 border-brand-primary text-brand-primary'
                    }`}
                    title={isDone ? 'Mark milestone incomplete' : 'Mark milestone done'}
                  >
                    {isDone ? <CheckCircle2 className="w-4 h-4" /> : step.stepNumber}
                  </button>

                  {/* Step Card */}
                  <div
                    className={`flex-1 p-3.5 rounded-xl border transition-all ${
                      isDone
                        ? 'bg-surface-secondary/40 border-edge-light dark:border-edge-dark opacity-75'
                        : 'bg-white dark:bg-surface-darkCard border-edge-light dark:border-edge-dark shadow-xs'
                    }`}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h6
                        className={`text-sm font-semibold ${
                          isDone ? 'line-through text-content-secondary' : 'text-content-primary dark:text-content-darkPrimary'
                        }`}
                      >
                        {step.title}
                      </h6>

                      <div className="flex items-center gap-2 text-xs text-content-secondary">
                        {step.suggestedTiming && (
                          <span className="flex items-center gap-1 font-medium bg-surface-secondary dark:bg-surface-darkSecondary px-2 py-0.5 rounded border border-edge-light dark:border-edge-dark">
                            <Clock className="w-3 h-3" />
                            {step.suggestedTiming}
                          </span>
                        )}
                        {step.owner && (
                          <span className="flex items-center gap-1 font-medium text-content-primary dark:text-content-darkPrimary">
                            <User className="w-3 h-3 text-content-secondary" />
                            {step.owner}
                          </span>
                        )}
                      </div>
                    </div>

                    {step.description && (
                      <p className="text-xs text-content-secondary dark:text-content-darkSecondary mt-1 leading-relaxed">
                        {step.description}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Check-in Milestones */}
        {plan.checkInDates && plan.checkInDates.length > 0 && (
          <div className="pt-3 border-t border-edge-light dark:border-edge-dark flex items-center justify-between text-xs text-content-secondary">
            <span className="font-medium">Scheduled Check-in Sync Dates:</span>
            <div className="flex items-center gap-2">
              {plan.checkInDates.map((date, i) => (
                <span
                  key={i}
                  className="px-2.5 py-1 rounded-lg bg-surface-secondary dark:bg-surface-darkSecondary border border-edge-light dark:border-edge-dark font-mono text-[11px]"
                >
                  {date}
                </span>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
