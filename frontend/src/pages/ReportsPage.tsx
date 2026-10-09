import React, { useState, useMemo } from 'react';
import {
  FileBarChart,
  Download,
  FileText,
  Calendar,
  Layers,
  Sparkles,
  CheckCircle2,
  ListTodo,
  Milestone,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Select, Input } from '../components/ui/Input';
import {
  exportMeetingAsPdf,
  exportAsTxt,
  exportAsJson,
  exportDecisionsCsv,
  exportActionItemsCsv,
  generateMeetingMarkdown,
  downloadBlob,
} from '../utils/exportHelpers';
import { formatDateTime, formatDuration } from '../utils/formatters';
import { useData } from '../context/DataContext';
import { toast } from 'sonner';

export const ReportsPage: React.FC = () => {
  const { meetings, decisions, actionItems, followUps, getTranscript, getAnalysis } = useData();

  const [selectedMeetingId, setSelectedMeetingId] = useState<string>(
    meetings[0]?.id || ''
  );
  const [reportFormat, setReportFormat] = useState<'pdf' | 'markdown' | 'json' | 'txt' | 'csv'>(
    'pdf'
  );
  const [includeTranscript, setIncludeTranscript] = useState(true);
  const [includeDecisions, setIncludeDecisions] = useState(true);
  const [includeActions, setIncludeActions] = useState(true);
  const [includeFollowUp, setIncludeFollowUp] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  const selectedMeeting = meetings.find((m) => m.id === selectedMeetingId);

  const meetingDecisions = useMemo(() => {
    if (!selectedMeetingId) return decisions;
    return decisions.filter((d) => d.meetingId === selectedMeetingId);
  }, [decisions, selectedMeetingId]);

  const meetingActions = useMemo(() => {
    if (!selectedMeetingId) return actionItems;
    return actionItems.filter((a) => a.meetingId === selectedMeetingId);
  }, [actionItems, selectedMeetingId]);

  const meetingFollowUp = useMemo(() => {
    if (!selectedMeetingId) return followUps[0];
    return followUps.find((f) => f.meetingId === selectedMeetingId);
  }, [followUps, selectedMeetingId]);

  const handleGenerateAndExport = async () => {
    if (!selectedMeeting) {
      toast.error('Please select a meeting to generate report');
      return;
    }

    setIsExporting(true);
    try {
      const [transcript, analysis] = await Promise.all([
        getTranscript(selectedMeeting.id),
        getAnalysis(selectedMeeting.id),
      ]);

      const baseName = selectedMeeting.title.replace(/[^a-zA-Z0-9_-]/g, '_');

      if (reportFormat === 'pdf') {
        exportMeetingAsPdf(
          selectedMeeting,
          analysis || undefined,
          includeDecisions ? meetingDecisions : undefined,
          includeActions ? meetingActions : undefined,
          includeFollowUp ? meetingFollowUp : undefined
        );
        toast.success('Generated PDF Report');
      } else if (reportFormat === 'markdown') {
        const md = generateMeetingMarkdown(
          selectedMeeting,
          includeTranscript ? transcript || undefined : undefined,
          analysis || undefined,
          includeDecisions ? meetingDecisions : undefined,
          includeActions ? meetingActions : undefined,
          includeFollowUp ? meetingFollowUp : undefined
        );
        downloadBlob(md, `${baseName}_report.md`, 'text/markdown;charset=utf-8');
        toast.success('Exported Markdown summary');
      } else if (reportFormat === 'json') {
        const payload = {
          meeting: selectedMeeting,
          analysis,
          decisions: includeDecisions ? meetingDecisions : [],
          actionItems: includeActions ? meetingActions : [],
          followUpPlan: includeFollowUp ? meetingFollowUp : null,
          transcript: includeTranscript ? transcript : null,
        };
        exportAsJson(payload, `${baseName}_data.json`);
        toast.success('Exported JSON structured dataset');
      } else if (reportFormat === 'txt') {
        if (transcript?.text) {
          exportAsTxt(transcript.text, `${baseName}_transcript.txt`);
          toast.success('Downloaded transcript TXT');
        } else {
          toast.error('No transcript text available');
        }
      } else if (reportFormat === 'csv') {
        exportDecisionsCsv(meetingDecisions, `${baseName}_decisions.csv`);
        toast.success('Exported tabular decisions CSV');
      }
    } catch (err: any) {
      toast.error(`Export failed: ${err.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-content-primary dark:text-content-darkPrimary flex items-center gap-2.5">
            <FileBarChart className="w-6 h-6 text-brand-primary" />
            Executive Reports & Exports
          </h1>
          <p className="text-xs sm:text-sm text-content-secondary dark:text-content-darkSecondary mt-0.5">
            Generate printable PDF briefs, Markdown summaries, CSV spreadsheets, and structured JSON
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls Column */}
        <div className="space-y-6">
          <Card className="p-5 space-y-4">
            <h3 className="text-sm font-semibold text-content-primary uppercase tracking-wider">
              Report Parameters
            </h3>

            <Select
              label="Select Target Meeting"
              value={selectedMeetingId}
              onChange={(e) => setSelectedMeetingId(e.target.value)}
            >
              {meetings.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.title}
                </option>
              ))}
            </Select>

            <Select
              label="Export Format"
              value={reportFormat}
              onChange={(e) => setReportFormat(e.target.value as any)}
            >
              <option value="pdf">PDF Document (.pdf) - Executive Layout</option>
              <option value="markdown">Markdown (.md) - Documentation</option>
              <option value="json">JSON (.json) - Full Data Schema</option>
              <option value="txt">TXT (.txt) - Plain Transcript</option>
              <option value="csv">CSV (.csv) - Spreadsheet Decisions</option>
            </Select>

            <div className="space-y-2 pt-2 border-t border-edge-light dark:border-edge-dark">
              <label className="text-xs font-semibold text-content-secondary block">
                Include Sections:
              </label>

              <label className="flex items-center gap-2 text-xs text-content-primary cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeTranscript}
                  onChange={(e) => setIncludeTranscript(e.target.checked)}
                  className="rounded text-brand-primary focus:ring-brand-primary"
                />
                Full Transcript Text
              </label>

              <label className="flex items-center gap-2 text-xs text-content-primary cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeDecisions}
                  onChange={(e) => setIncludeDecisions(e.target.checked)}
                  className="rounded text-brand-primary focus:ring-brand-primary"
                />
                Confirmed Decisions & Supporting Evidence
              </label>

              <label className="flex items-center gap-2 text-xs text-content-primary cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeActions}
                  onChange={(e) => setIncludeActions(e.target.checked)}
                  className="rounded text-brand-primary focus:ring-brand-primary"
                />
                Action Items & Assigned Deadlines
              </label>

              <label className="flex items-center gap-2 text-xs text-content-primary cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeFollowUp}
                  onChange={(e) => setIncludeFollowUp(e.target.checked)}
                  className="rounded text-brand-primary focus:ring-brand-primary"
                />
                Follow-up Plan Milestones
              </label>
            </div>

            <Button
              variant="primary"
              className="w-full justify-center"
              isLoading={isExporting}
              onClick={handleGenerateAndExport}
              leftIcon={<Download className="w-4 h-4" />}
            >
              Export Report
            </Button>
          </Card>
        </div>

        {/* Live Report Preview Column */}
        <div className="lg:col-span-2">
          <Card className="overflow-hidden border-brand-primary/20">
            <CardHeader>
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-brand-primary" />
                <CardTitle>Report Preview</CardTitle>
              </div>
              <span className="text-xs font-mono uppercase text-content-secondary">
                Format: {reportFormat.toUpperCase()}
              </span>
            </CardHeader>

            <CardContent className="space-y-6 bg-white dark:bg-surface-darkCard p-6 sm:p-8 font-sans">
              {selectedMeeting ? (
                <div className="space-y-6">
                  {/* Title & Metadata Header */}
                  <div className="border-b border-edge-light dark:border-edge-dark pb-4">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-brand-primary">
                      MeetMind Executive Brief
                    </span>
                    <h2 className="text-xl sm:text-2xl font-bold text-content-primary mt-1">
                      {selectedMeeting.title}
                    </h2>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-content-secondary mt-1.5">
                      <span>Date: {formatDateTime(selectedMeeting.meetingDate)}</span>
                      <span>•</span>
                      <span>Duration: {formatDuration(selectedMeeting.durationSeconds)}</span>
                      <span>•</span>
                      <span>Type: {selectedMeeting.meetingType}</span>
                    </div>
                  </div>

                  {/* Summary Preview */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-content-secondary">
                      Executive Summary
                    </h4>
                    <p className="text-xs sm:text-sm text-content-primary leading-relaxed bg-surface-secondary/40 dark:bg-surface-darkSecondary/30 p-4 rounded-xl border border-edge-light dark:border-edge-dark">
                      Leadership aligned on core roadmap deliverables, container optimization ceilings, and migration documentation. Concrete action owners were assigned with zero timeline slippage.
                    </p>
                  </div>

                  {/* Decisions Preview */}
                  {includeDecisions && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-content-secondary">
                        Decisions Captured ({meetingDecisions.length})
                      </h4>
                      <div className="space-y-2">
                        {meetingDecisions.map((d) => (
                          <div
                            key={d.id}
                            className="p-3 rounded-xl border border-edge-light dark:border-edge-dark text-xs flex items-start justify-between gap-3"
                          >
                            <div>
                              <p className="font-semibold text-content-primary">{d.title}</p>
                              <p className="text-content-secondary mt-0.5">{d.description}</p>
                            </div>
                            <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 shrink-0">
                              {d.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Action Items Preview */}
                  {includeActions && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-content-secondary">
                        Action Items & Deadlines ({meetingActions.length})
                      </h4>
                      <div className="space-y-2">
                        {meetingActions.map((a) => (
                          <div
                            key={a.id}
                            className="p-3 rounded-xl border border-edge-light dark:border-edge-dark text-xs flex items-center justify-between gap-3"
                          >
                            <div>
                              <p className="font-semibold text-content-primary">{a.title}</p>
                              <p className="text-content-secondary mt-0.5">
                                Assignee: {a.assignee || 'Unassigned'}
                              </p>
                            </div>
                            <span className="text-[10px] font-semibold text-brand-primary bg-brand-light px-2 py-0.5 rounded-full border border-brand-primary/20 shrink-0">
                              {a.priority}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="py-12 text-center text-xs text-content-secondary">
                  Select a meeting to view preview
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
