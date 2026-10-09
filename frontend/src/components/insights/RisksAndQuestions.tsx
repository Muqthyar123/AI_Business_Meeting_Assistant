import React, { useState } from 'react';
import {
  AlertTriangle,
  HelpCircle,
  ArrowRight,
  Send,
  CheckCircle2,
  Edit2,
  ListTodo,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { useData } from '../../context/DataContext';
import { toast } from 'sonner';

interface RisksAndQuestionsProps {
  risks: string[];
  openQuestions: string[];
  suggestedNextSteps: string[];
  meetingId?: string;
  meetingTitle?: string;
}

export const RisksAndQuestions: React.FC<RisksAndQuestionsProps> = ({
  risks,
  openQuestions,
  suggestedNextSteps,
  meetingId,
  meetingTitle,
}) => {
  const { createActionItem } = useData();

  // Load persisted question answers from localStorage if available
  const storageKey = `meetmind_answers_${meetingId || 'general'}`;
  const [answers, setAnswers] = useState<Record<number, string>>(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  const [inputValues, setInputValues] = useState<Record<number, string>>(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  const handleSaveAnswer = async (question: string, index: number) => {
    const answerText = (inputValues[index] || '').trim();
    if (!answerText) {
      toast.error('Please enter an answer before updating tasks.');
      return;
    }

    const updatedAnswers = { ...answers, [index]: answerText };
    setAnswers(updatedAnswers);
    setEditingIndex(null);

    try {
      localStorage.setItem(storageKey, JSON.stringify(updatedAnswers));
    } catch (e) {
      console.warn('Failed to save answer to localStorage', e);
    }

    // Automatically create or update an Action Item Task from the resolved answer
    try {
      await createActionItem({
        title: `Resolve: ${question.length > 50 ? question.substring(0, 50) + '...' : question}`,
        description: `Open Question: "${question}"\n\nConfirmed Answer & Resolution: ${answerText}`,
        priority: 'High',
        status: 'In Progress',
        meetingId: meetingId || 'general',
        meetingTitle: meetingTitle || 'Meeting Insights',
        evidence: `Resolution to open question: "${question}"`,
        isManual: true,
      });

      toast.success('Answer saved and corresponding action task updated on the board!');
    } catch (err: any) {
      toast.error(`Answer saved, but task update failed: ${err.message}`);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Risks & Blockers */}
      <Card className="border-amber-200 dark:border-amber-900/40">
        <CardHeader className="bg-amber-50/50 dark:bg-amber-950/20">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            <CardTitle className="text-amber-900 dark:text-amber-200">
              Identified Risks
            </CardTitle>
          </div>
          <CardDescription>Potential bottlenecks or execution friction</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 pt-4">
          {risks.length === 0 ? (
            <p className="text-xs text-content-secondary">No critical risks flagged.</p>
          ) : (
            risks.map((risk, i) => (
              <div
                key={i}
                className="p-3 rounded-xl bg-amber-50/60 dark:bg-amber-950/30 border border-amber-200/80 dark:border-amber-800/40 text-xs text-amber-900 dark:text-amber-200 leading-relaxed"
              >
                {risk}
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {/* Unresolved Questions & Interactive Answer Input */}
      <Card className="border-sky-200 dark:border-sky-900/40">
        <CardHeader className="bg-sky-50/50 dark:bg-sky-950/20">
          <div className="flex items-center gap-2">
            <HelpCircle className="w-4 h-4 text-sky-600 dark:text-sky-400" />
            <CardTitle className="text-sky-900 dark:text-sky-200">
              Open Questions
            </CardTitle>
          </div>
          <CardDescription>Answer questions to resolve blockers and update tasks</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 pt-4">
          {openQuestions.length === 0 ? (
            <p className="text-xs text-content-secondary">No unresolved questions flagged.</p>
          ) : (
            openQuestions.map((q, i) => {
              const hasAnswer = Boolean(answers[i]);
              const isEditing = editingIndex === i || !hasAnswer;

              return (
                <div
                  key={i}
                  className="p-3.5 rounded-xl bg-sky-50/60 dark:bg-sky-950/30 border border-sky-200/80 dark:border-sky-800/40 text-xs space-y-2.5 transition-all"
                >
                  {/* Question Title */}
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-semibold text-sky-950 dark:text-sky-100 leading-relaxed">
                      {q}
                    </p>
                    {hasAnswer && !isEditing && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-100 dark:bg-emerald-950/60 px-2 py-0.5 rounded-full shrink-0">
                        <CheckCircle2 className="w-3 h-3" />
                        Answered
                      </span>
                    )}
                  </div>

                  {/* Confirmed Answer display (if already answered and not editing) */}
                  {hasAnswer && !isEditing && (
                    <div className="p-2.5 rounded-lg bg-white/80 dark:bg-surface-darkSecondary/60 border border-sky-200/60 dark:border-sky-800/40 space-y-1.5">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Confirmed Resolution:
                        </span>
                        <button
                          type="button"
                          onClick={() => setEditingIndex(i)}
                          className="text-brand-primary hover:underline flex items-center gap-1 text-[11px]"
                        >
                          <Edit2 className="w-3 h-3" />
                          Edit
                        </button>
                      </div>
                      <p className="text-xs text-content-primary dark:text-content-darkPrimary leading-relaxed">
                        {answers[i]}
                      </p>
                    </div>
                  )}

                  {/* Answer Input Field */}
                  {isEditing && (
                    <div className="space-y-2 pt-1">
                      <textarea
                        value={inputValues[i] || ''}
                        onChange={(e) =>
                          setInputValues((prev) => ({ ...prev, [i]: e.target.value }))
                        }
                        placeholder="Type answer or decision to resolve this question..."
                        rows={2}
                        className="w-full rounded-lg border border-sky-300 dark:border-sky-700 bg-white dark:bg-surface-darkCard p-2 text-xs text-content-primary focus:outline-none focus:ring-2 focus:ring-sky-500/30 resize-none leading-relaxed"
                      />

                      <div className="flex items-center justify-end gap-2">
                        {hasAnswer && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-7 text-xs px-2"
                            onClick={() => setEditingIndex(null)}
                          >
                            Cancel
                          </Button>
                        )}
                        <Button
                          type="button"
                          variant="primary"
                          size="sm"
                          className="h-7 text-xs px-3 bg-sky-600 hover:bg-sky-700 text-white"
                          leftIcon={<ListTodo className="w-3.5 h-3.5" />}
                          onClick={() => handleSaveAnswer(q, i)}
                        >
                          Submit & Update Task
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </CardContent>
      </Card>

      {/* Suggested Next Steps */}
      <Card className="border-indigo-200 dark:border-indigo-900/40">
        <CardHeader className="bg-brand-light/50 dark:bg-brand-primary/10">
          <div className="flex items-center gap-2">
            <ArrowRight className="w-4 h-4 text-brand-primary dark:text-brand-secondary" />
            <CardTitle className="text-content-primary dark:text-content-darkPrimary">
              Suggested Next Steps
            </CardTitle>
          </div>
          <CardDescription>Recommended tactical follow-ups</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 pt-4">
          {suggestedNextSteps.length === 0 ? (
            <p className="text-xs text-content-secondary">No explicit next steps generated.</p>
          ) : (
            suggestedNextSteps.map((step, i) => (
              <div
                key={i}
                className="p-3 rounded-xl bg-brand-light/30 dark:bg-brand-primary/10 border border-brand-primary/20 text-xs text-content-primary dark:text-content-darkPrimary leading-relaxed"
              >
                {step}
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
};
