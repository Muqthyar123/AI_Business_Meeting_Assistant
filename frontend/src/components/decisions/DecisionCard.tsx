import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, User, Calendar, Quote, MoreHorizontal, Edit, Trash2, ExternalLink } from 'lucide-react';
import { Decision, DecisionStatus } from '../../types';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { DECISION_STATUS_CONFIG } from '../../config/constants';
import { formatDate } from '../../utils/formatters';
import { useData } from '../../context/DataContext';

interface DecisionCardProps {
  decision: Decision;
  onEdit: (decision: Decision) => void;
}

export const DecisionCard: React.FC<DecisionCardProps> = ({ decision, onEdit }) => {
  const { updateDecision, deleteDecision } = useData();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const statusConfig = DECISION_STATUS_CONFIG[decision.status] || {
    label: decision.status,
    bg: 'bg-slate-100',
    text: 'text-slate-700',
    border: 'border-slate-200',
  };

  const handleStatusChange = (newStatus: DecisionStatus) => {
    updateDecision(decision.id, { status: newStatus });
    setIsMenuOpen(false);
  };

  const handleDelete = () => {
    if (window.confirm(`Are you sure you want to delete decision: "${decision.title}"?`)) {
      deleteDecision(decision.id);
    }
    setIsMenuOpen(false);
  };

  return (
    <Card className="p-5 flex flex-col justify-between hover:border-brand-primary/40 transition-all">
      <div>
        {/* Top Header: Category, Status & Menu */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <span
              className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${statusConfig.bg} ${statusConfig.text} ${statusConfig.border}`}
            >
              {decision.status}
            </span>

            {decision.category && (
              <span className="text-[11px] font-medium px-2 py-0.5 rounded-md bg-surface-secondary dark:bg-surface-darkSecondary text-content-secondary border border-edge-light dark:border-edge-dark">
                {decision.category}
              </span>
            )}

            {decision.isManual && (
              <span className="text-[10px] text-content-secondary/80 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">
                Manual
              </span>
            )}
          </div>

          <div className="relative">
            <button
              onClick={() => setIsMenuOpen((prev) => !prev)}
              className="p-1 rounded-lg text-content-secondary hover:text-content-primary hover:bg-surface-secondary dark:hover:bg-surface-darkSecondary transition-colors"
              title="Actions"
            >
              <MoreHorizontal className="w-4 h-4" />
            </button>

            {isMenuOpen && (
              <div className="absolute right-0 top-7 w-44 rounded-xl bg-white dark:bg-surface-darkCard border border-edge-light dark:border-edge-dark shadow-xl z-20 py-1.5 text-xs">
                <div className="px-3 py-1 text-[10px] uppercase font-bold text-content-secondary">
                  Set Status
                </div>
                {(['Confirmed', 'Proposed', 'Rejected', 'Superseded'] as DecisionStatus[]).map(
                  (s) => (
                    <button
                      key={s}
                      onClick={() => handleStatusChange(s)}
                      className={`w-full text-left px-3 py-1.5 hover:bg-surface-secondary dark:hover:bg-surface-darkSecondary flex items-center justify-between ${
                        decision.status === s ? 'font-semibold text-brand-primary' : ''
                      }`}
                    >
                      {s}
                      {decision.status === s && <CheckCircle2 className="w-3.5 h-3.5" />}
                    </button>
                  )
                )}

                <div className="my-1 border-t border-edge-light dark:border-edge-dark" />

                <button
                  onClick={() => {
                    setIsMenuOpen(false);
                    onEdit(decision);
                  }}
                  className="w-full text-left px-3 py-1.5 hover:bg-surface-secondary dark:hover:bg-surface-darkSecondary flex items-center gap-2"
                >
                  <Edit className="w-3.5 h-3.5" />
                  Edit Decision
                </button>

                <button
                  onClick={handleDelete}
                  className="w-full text-left px-3 py-1.5 hover:bg-rose-50 dark:hover:bg-rose-950/40 text-rose-600 flex items-center gap-2"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  Delete
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Title & Description */}
        <h4 className="text-base font-semibold text-content-primary dark:text-content-darkPrimary tracking-tight">
          {decision.title}
        </h4>
        <p className="text-xs sm:text-sm text-content-secondary dark:text-content-darkSecondary mt-2 leading-relaxed">
          {decision.description}
        </p>

        {/* Supporting Context Excerpt */}
        {decision.evidence && (
          <div className="mt-3 p-3 rounded-xl bg-surface-secondary/50 dark:bg-surface-darkSecondary/40 border border-edge-light dark:border-edge-dark flex items-start gap-2 text-xs italic text-content-secondary">
            <Quote className="w-3.5 h-3.5 text-brand-primary shrink-0 mt-0.5 not-italic" />
            <span className="line-clamp-2">&ldquo;{decision.evidence}&rdquo;</span>
          </div>
        )}
      </div>

      {/* Footer Info: Meeting & Owner */}
      <div className="mt-4 pt-3 border-t border-edge-light dark:border-edge-dark flex flex-wrap items-center justify-between gap-2 text-xs text-content-secondary dark:text-content-darkSecondary">
        <div className="flex items-center gap-2 truncate max-w-[220px]">
          {decision.meetingId && decision.meetingId !== 'general' ? (
            <Link
              to={`/meetings/${decision.meetingId}`}
              className="inline-flex items-center gap-1 hover:text-brand-primary transition-colors truncate font-medium"
              title="Open source meeting"
            >
              <span>{decision.meetingTitle || 'View Meeting'}</span>
              <ExternalLink className="w-3 h-3 shrink-0" />
            </Link>
          ) : (
            <span>Manual entry</span>
          )}
        </div>

        <div className="flex items-center gap-3 shrink-0 text-[11px]">
          {decision.owner && (
            <span className="flex items-center gap-1 font-medium text-content-primary dark:text-content-darkPrimary">
              <User className="w-3 h-3 text-content-secondary" />
              {decision.owner}
            </span>
          )}
          <span>{formatDate(decision.createdAt)}</span>
        </div>
      </div>
    </Card>
  );
};
