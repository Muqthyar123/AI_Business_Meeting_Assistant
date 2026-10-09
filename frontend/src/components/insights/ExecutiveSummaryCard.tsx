import React from 'react';
import { Sparkles, RefreshCw, Cpu, CheckCircle2, FileText } from 'lucide-react';
import { Analysis, Meeting } from '../../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { formatDateTime } from '../../utils/formatters';

interface ExecutiveSummaryCardProps {
  meeting: Meeting;
  analysis?: Analysis;
  onAnalyze: () => void;
  isAnalyzing: boolean;
}

export const ExecutiveSummaryCard: React.FC<ExecutiveSummaryCardProps> = ({
  meeting,
  analysis,
  onAnalyze,
  isAnalyzing,
}) => {
  return (
    <Card className="relative overflow-hidden border-brand-primary/20 dark:border-brand-primary/30">
      <div className="absolute top-0 right-0 w-64 h-64 bg-brand-primary/5 rounded-full blur-3xl -z-10 pointer-events-none" />

      <CardHeader>
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-brand-light dark:bg-brand-primary/20 text-brand-primary dark:text-brand-secondary flex items-center justify-center">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <CardTitle>Executive Summary & Purpose</CardTitle>
            <CardDescription>
              Synthesized by Groq Llama-3.3-70b via LangGraph multi-agent workflow
            </CardDescription>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {analysis && (
            <Badge variant="indigo" size="sm" dot>
              AI Verified
            </Badge>
          )}

          <Button
            variant={analysis ? 'outline' : 'primary'}
            size="sm"
            isLoading={isAnalyzing}
            onClick={onAnalyze}
            leftIcon={analysis ? <RefreshCw className="w-3.5 h-3.5" /> : <Sparkles className="w-3.5 h-3.5" />}
          >
            {analysis ? 'Reanalyze Meeting' : 'Analyze Meeting'}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {analysis?.purpose && (
          <div className="p-3.5 rounded-xl bg-surface-secondary/60 dark:bg-surface-darkSecondary/40 border border-edge-light dark:border-edge-dark">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-content-secondary dark:text-content-darkSecondary block mb-1">
              Primary Meeting Objective
            </span>
            <p className="text-sm font-medium text-content-primary dark:text-content-darkPrimary">
              {analysis.purpose}
            </p>
          </div>
        )}

        {analysis?.summary ? (
          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-content-secondary dark:text-content-darkSecondary block mb-1.5">
              Executive Briefing
            </span>
            <p className="text-sm sm:text-base leading-relaxed text-content-primary dark:text-content-darkPrimary">
              {analysis.summary}
            </p>
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-content-secondary dark:text-content-darkSecondary">
            This meeting transcript has not been analyzed yet. Click &ldquo;Analyze Meeting&rdquo; to extract key discussion points, decisions, and follow-ups.
          </div>
        )}

        {analysis && (
          <div className="pt-3 border-t border-edge-light dark:border-edge-dark flex flex-wrap items-center justify-between gap-2 text-[11px] text-content-secondary dark:text-content-darkSecondary">
            <span className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-brand-primary" />
              Engine: {analysis.modelUsed || 'Groq Llama-3.3-70b-versatile via LangGraph'}
            </span>
            <span>Generated: {formatDateTime(analysis.updatedAt)}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
