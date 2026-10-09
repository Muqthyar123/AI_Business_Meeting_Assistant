import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Calendar, CheckCircle2, ListTodo, FileText, ArrowRight, X } from 'lucide-react';
import { useData } from '../../context/DataContext';
import { truncateText } from '../../utils/formatters';

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const GlobalSearchModal: React.FC<GlobalSearchModalProps> = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();
  const { meetings, decisions, actionItems } = useData();

  useEffect(() => {
    if (!isOpen) {
      setQuery('');
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else {
          // Open triggered by parent
        }
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const searchResults = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return null;

    const matchedMeetings = meetings.filter(
      (m) =>
        m.title.toLowerCase().includes(q) ||
        (m.description && m.description.toLowerCase().includes(q)) ||
        m.participants.some((p) => p.toLowerCase().includes(q))
    ).slice(0, 4);

    const matchedDecisions = decisions.filter(
      (d) =>
        d.title.toLowerCase().includes(q) ||
        d.description.toLowerCase().includes(q) ||
        (d.evidence && d.evidence.toLowerCase().includes(q))
    ).slice(0, 4);

    const matchedActionItems = actionItems.filter(
      (a) =>
        a.title.toLowerCase().includes(q) ||
        (a.description && a.description.toLowerCase().includes(q)) ||
        (a.assignee && a.assignee.toLowerCase().includes(q))
    ).slice(0, 4);

    const totalCount =
      matchedMeetings.length + matchedDecisions.length + matchedActionItems.length;

    return {
      meetings: matchedMeetings,
      decisions: matchedDecisions,
      actionItems: matchedActionItems,
      totalCount,
    };
  }, [query, meetings, decisions, actionItems]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4 sm:p-6 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal Dialog */}
      <div className="relative w-full max-w-2xl rounded-2xl bg-white dark:bg-surface-darkCard border border-edge-light dark:border-edge-dark shadow-2xl overflow-hidden z-10 animate-in fade-in zoom-in-95 duration-150">
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3.5 border-b border-edge-light dark:border-edge-dark gap-3">
          <Search className="w-5 h-5 text-content-secondary dark:text-content-darkSecondary shrink-0" />
          <input
            type="text"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search meetings, transcripts, decisions, and action items..."
            className="flex-1 bg-transparent text-sm text-content-primary dark:text-content-darkPrimary placeholder:text-content-secondary/60 focus:outline-none"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="p-1 rounded-md text-content-secondary hover:text-content-primary"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <kbd className="hidden sm:inline-block px-2 py-0.5 text-[10px] font-mono rounded bg-surface-secondary dark:bg-surface-darkSecondary text-content-secondary border border-edge-light dark:border-edge-dark">
            ESC
          </kbd>
        </div>

        {/* Results Area */}
        <div className="max-h-[60vh] overflow-y-auto p-4 space-y-4">
          {!query && (
            <div className="py-8 text-center text-xs text-content-secondary dark:text-content-darkSecondary">
              <p>Type to search across all meetings, decisions, and tasks.</p>
              <p className="mt-1 opacity-70">
                Tip: Search by attendee name, project keyword, or decision topic.
              </p>
            </div>
          )}

          {query && searchResults && searchResults.totalCount === 0 && (
            <div className="py-8 text-center text-xs text-content-secondary dark:text-content-darkSecondary">
              No results found for &ldquo;<span className="font-semibold">{query}</span>&rdquo;.
            </div>
          )}

          {searchResults && searchResults.meetings.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-content-secondary dark:text-content-darkSecondary px-2 mb-1.5 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-brand-primary" />
                Meetings ({searchResults.meetings.length})
              </p>
              <div className="space-y-1">
                {searchResults.meetings.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => {
                      navigate(`/meetings/${m.id}`);
                      onClose();
                    }}
                    className="w-full text-left p-2.5 rounded-xl hover:bg-surface-secondary dark:hover:bg-surface-darkSecondary/70 transition-colors flex items-center justify-between group"
                  >
                    <div>
                      <p className="text-sm font-medium text-content-primary dark:text-content-darkPrimary group-hover:text-brand-primary transition-colors">
                        {m.title}
                      </p>
                      <p className="text-xs text-content-secondary dark:text-content-darkSecondary">
                        {m.meetingType} • {m.participants.slice(0, 2).join(', ')}
                      </p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-content-secondary opacity-0 group-hover:opacity-100 transition-opacity" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {searchResults && searchResults.decisions.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-content-secondary dark:text-content-darkSecondary px-2 mb-1.5 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                Decisions ({searchResults.decisions.length})
              </p>
              <div className="space-y-1">
                {searchResults.decisions.map((d) => (
                  <button
                    key={d.id}
                    onClick={() => {
                      navigate('/decisions');
                      onClose();
                    }}
                    className="w-full text-left p-2.5 rounded-xl hover:bg-surface-secondary dark:hover:bg-surface-darkSecondary/70 transition-colors flex items-center justify-between group"
                  >
                    <div>
                      <p className="text-sm font-medium text-content-primary dark:text-content-darkPrimary group-hover:text-brand-primary transition-colors">
                        {d.title}
                      </p>
                      <p className="text-xs text-content-secondary dark:text-content-darkSecondary">
                        {truncateText(d.description, 90)}
                      </p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-content-secondary opacity-0 group-hover:opacity-100 transition-opacity" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {searchResults && searchResults.actionItems.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-content-secondary dark:text-content-darkSecondary px-2 mb-1.5 flex items-center gap-1.5">
                <ListTodo className="w-3.5 h-3.5 text-brand-secondary" />
                Action Items ({searchResults.actionItems.length})
              </p>
              <div className="space-y-1">
                {searchResults.actionItems.map((a) => (
                  <button
                    key={a.id}
                    onClick={() => {
                      navigate('/action-items');
                      onClose();
                    }}
                    className="w-full text-left p-2.5 rounded-xl hover:bg-surface-secondary dark:hover:bg-surface-darkSecondary/70 transition-colors flex items-center justify-between group"
                  >
                    <div>
                      <p className="text-sm font-medium text-content-primary dark:text-content-darkPrimary group-hover:text-brand-primary transition-colors">
                        {a.title}
                      </p>
                      <p className="text-xs text-content-secondary dark:text-content-darkSecondary">
                        Assignee: {a.assignee || 'Unassigned'} • Status: {a.status}
                      </p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-content-secondary opacity-0 group-hover:opacity-100 transition-opacity" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 border-t border-edge-light dark:border-edge-dark bg-surface-secondary/40 dark:bg-surface-darkSecondary/30 text-[11px] text-content-secondary dark:text-content-darkSecondary flex items-center justify-between">
          <span>Navigate with mouse or keyboard</span>
          <span>MeetMind Unified Search</span>
        </div>
      </div>
    </div>
  );
};
