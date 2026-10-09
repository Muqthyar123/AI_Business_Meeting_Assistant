import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Calendar, ArrowRight, RefreshCw, Cpu, Layers } from 'lucide-react';
import { ExecutiveSummaryCard } from '../components/insights/ExecutiveSummaryCard';
import { KeyPointsSection } from '../components/insights/KeyPointsSection';
import { RisksAndQuestions } from '../components/insights/RisksAndQuestions';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { useData } from '../context/DataContext';
import { formatDateTime, formatDuration } from '../utils/formatters';

export const InsightsPage: React.FC = () => {
  const navigate = useNavigate();
  const { meetings, getAnalysis, triggerAnalysis } = useData();

  const [selectedMeetingId, setSelectedMeetingId] = useState<string>(
    meetings[0]?.id || ''
  );
  const [analysis, setAnalysis] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  useEffect(() => {
    if (meetings.length > 0 && !selectedMeetingId) {
      setSelectedMeetingId(meetings[0].id);
    }
  }, [meetings, selectedMeetingId]);

  const selectedMeeting = meetings.find((m) => m.id === selectedMeetingId);

  useEffect(() => {
    if (!selectedMeetingId) return;

    let isMounted = true;
    const fetchAnalysis = async () => {
      const ans = await getAnalysis(selectedMeetingId);
      if (isMounted) setAnalysis(ans || null);
    };

    fetchAnalysis();
    return () => {
      isMounted = false;
    };
  }, [selectedMeetingId, getAnalysis]);

  const handleTriggerAnalysis = async () => {
    if (!selectedMeetingId) return;
    setIsAnalyzing(true);
    try {
      const res = await triggerAnalysis(selectedMeetingId);
      setAnalysis(res);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-content-primary dark:text-content-darkPrimary flex items-center gap-2.5">
            <Sparkles className="w-6 h-6 text-brand-primary" />
            AI Meeting Insights
          </h1>
          <p className="text-xs sm:text-sm text-content-secondary dark:text-content-darkSecondary mt-0.5">
            Groq Llama-3.3-70b and LangGraph extraction of decisions, key points, and risk factors
          </p>
        </div>

        {/* Meeting Selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-content-secondary shrink-0">
            Selected Meeting:
          </label>
          <select
            value={selectedMeetingId}
            onChange={(e) => setSelectedMeetingId(e.target.value)}
            className="text-xs sm:text-sm px-3 py-2 rounded-xl border border-edge-light dark:border-edge-dark bg-white dark:bg-surface-darkSecondary text-content-primary focus:outline-none max-w-xs truncate"
          >
            {meetings.map((m) => (
              <option key={m.id} value={m.id}>
                {m.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {selectedMeeting ? (
        <div className="space-y-6">
          {/* Executive Summary Card */}
          <ExecutiveSummaryCard
            meeting={selectedMeeting}
            analysis={analysis || undefined}
            onAnalyze={handleTriggerAnalysis}
            isAnalyzing={isAnalyzing}
          />

          {analysis ? (
            <>
              {/* Key Discussion Points & Topics */}
              <KeyPointsSection
                keyPoints={analysis.keyPoints}
                topics={analysis.topics}
              />

              {/* Risks, Open Questions & Suggested Next Steps */}
              <RisksAndQuestions
                risks={analysis.risks}
                openQuestions={analysis.openQuestions}
                suggestedNextSteps={analysis.suggestedNextSteps}
                meetingId={selectedMeeting.id}
                meetingTitle={selectedMeeting.title}
              />
            </>
          ) : (
            <Card className="p-10 text-center space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-brand-light text-brand-primary flex items-center justify-center mx-auto">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-base font-semibold text-content-primary">
                Analysis Ready for &ldquo;{selectedMeeting.title}&rdquo;
              </h3>
              <p className="text-xs text-content-secondary max-w-md mx-auto">
                This meeting transcript is ready for multi-agent synthesis. Click below to generate an executive brief, identify decisions, and extract next steps.
              </p>
              <Button
                variant="primary"
                isLoading={isAnalyzing}
                onClick={handleTriggerAnalysis}
                leftIcon={<Sparkles className="w-4 h-4" />}
              >
                Analyze Meeting Now
              </Button>
            </Card>
          )}
        </div>
      ) : (
        <Card className="p-8 text-center text-xs text-content-secondary">
          No meetings available to analyze. Please upload an audio recording first.
        </Card>
      )}
    </div>
  );
};
