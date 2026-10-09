import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  Calendar,
  Clock,
  Users,
  Sparkles,
  FileText,
  CheckCircle2,
  ListTodo,
  Milestone,
  Download,
  Share2,
  Trash2,
  Edit,
  ArrowLeft,
  RefreshCw,
  Plus,
} from 'lucide-react';
import { Meeting, Transcript, Analysis, Decision, ActionItem, FollowUpPlan } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Tabs } from '../components/ui/Tabs';
import { Modal } from '../components/ui/Modal';
import { Input, Textarea, Select } from '../components/ui/Input';
import { TranscriptEditor } from '../components/transcription/TranscriptEditor';
import { ExecutiveSummaryCard } from '../components/insights/ExecutiveSummaryCard';
import { KeyPointsSection } from '../components/insights/KeyPointsSection';
import { RisksAndQuestions } from '../components/insights/RisksAndQuestions';
import { DecisionCard } from '../components/decisions/DecisionCard';
import { DecisionFormModal } from '../components/decisions/DecisionFormModal';
import { ActionItemList } from '../components/action-items/ActionItemList';
import { ActionItemFormModal } from '../components/action-items/ActionItemFormModal';
import { FollowUpTimeline } from '../components/follow-ups/FollowUpTimeline';
import { FollowUpFormModal } from '../components/follow-ups/FollowUpFormModal';
import { formatDateTime, formatDuration } from '../utils/formatters';
import { exportMeetingAsPdf, exportAsTxt, generateMeetingMarkdown, downloadBlob } from '../utils/exportHelpers';
import { MEETING_TYPES } from '../config/constants';
import { useData } from '../context/DataContext';
import { toast } from 'sonner';

export const MeetingDetailPage: React.FC = () => {
  const { meetingId } = useParams<{ meetingId: string }>();
  const navigate = useNavigate();
  const location = useLocation();

  const {
    getMeeting,
    updateMeeting,
    deleteMeeting,
    getTranscript,
    getAnalysis,
    triggerAnalysis,
    decisions,
    actionItems,
    followUps,
    refreshDecisions,
    refreshActionItems,
    refreshFollowUps,
    generateFollowUpPlan,
  } = useData();

  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Active Tab state
  const getInitialTab = () => {
    if (location.pathname.endsWith('/transcript')) return 'transcript';
    if (location.pathname.endsWith('/insights')) return 'insights';
    return 'overview';
  };
  const [activeTab, setActiveTab] = useState(getInitialTab);

  // Modals state
  const [isEditMetaOpen, setIsEditMetaOpen] = useState(false);
  const [isDecisionModalOpen, setIsDecisionModalOpen] = useState(false);
  const [selectedDecision, setSelectedDecision] = useState<Decision | null>(null);
  const [isActionModalOpen, setIsActionModalOpen] = useState(false);
  const [selectedAction, setSelectedAction] = useState<ActionItem | null>(null);
  const [isFollowUpModalOpen, setIsFollowUpModalOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<FollowUpPlan | null>(null);

  // Meta Edit form state
  const [editTitle, setEditTitle] = useState('');
  const [editType, setEditType] = useState('Team Meeting');
  const [editDept, setEditDept] = useState('');
  const [editDesc, setEditDesc] = useState('');

  // Fetch meeting data
  useEffect(() => {
    if (!meetingId) return;

    let isMounted = true;
    const loadData = async () => {
      setLoading(true);
      const m = await getMeeting(meetingId);
      if (m && isMounted) {
        setMeeting(m);
        setEditTitle(m.title);
        setEditType(m.meetingType);
        setEditDept(m.department || '');
        setEditDesc(m.description || '');

        const [t, a] = await Promise.all([
          getTranscript(meetingId),
          getAnalysis(meetingId),
        ]);
        if (isMounted) {
          setTranscript(t || null);
          setAnalysis(a || null);
        }
      }
      if (isMounted) setLoading(false);
    };

    loadData();
    return () => {
      isMounted = false;
    };
  }, [meetingId]);

  if (loading) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-8 h-8 rounded-full border-2 border-brand-primary border-t-transparent animate-spin mx-auto" />
        <p className="text-xs text-content-secondary">Loading meeting workspace...</p>
      </div>
    );
  }

  if (!meeting) {
    return (
      <div className="py-20 text-center space-y-4">
        <h2 className="text-lg font-bold text-content-primary">Meeting Not Found</h2>
        <p className="text-xs text-content-secondary">The requested meeting identifier does not exist.</p>
        <Button variant="primary" size="sm" onClick={() => navigate('/meetings')}>
          Return to Meetings
        </Button>
      </div>
    );
  }

  // Related decisions, actions, and follow-ups
  const meetingDecisions = decisions.filter(
    (d) => d.meetingId === meeting.id || (analysis && d.meetingId === analysis.id)
  );
  const meetingActions = actionItems.filter(
    (a) =>
      a.meetingId === meeting.id ||
      (analysis && a.meetingId === analysis.id) ||
      (meeting.transcriptionId && a.meetingId === meeting.transcriptionId)
  );
  const meetingFollowUp = followUps.find(
    (f) => f.meetingId === meeting.id || (analysis && f.meetingId === analysis.id)
  );

  const handleTriggerAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      const res = await triggerAnalysis(meeting.id);
      setAnalysis(res);
      setMeeting((prev) => (prev ? { ...prev, analysisStatus: 'completed' } : null));
      await Promise.all([
        refreshDecisions(res.id),
        refreshActionItems(res.id),
        refreshFollowUps(res.id),
      ]);
      toast.success('AI Meeting Analysis complete!');
      setActiveTab('insights');
    } catch (err: any) {
      toast.error(`Analysis failed: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSaveMeta = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editTitle.trim()) return;

    const updated = await updateMeeting(meeting.id, {
      title: editTitle.trim(),
      meetingType: editType as any,
      department: editDept.trim(),
      description: editDesc.trim(),
    });

    if (updated) {
      setMeeting(updated);
      toast.success('Meeting details updated');
      setIsEditMetaOpen(false);
    }
  };

  const handleDeleteMeeting = () => {
    if (window.confirm(`Permanently delete "${meeting.title}"?`)) {
      deleteMeeting(meeting.id);
      navigate('/meetings');
    }
  };

  const handleExportPdf = () => {
    exportMeetingAsPdf(
      meeting,
      analysis || undefined,
      meetingDecisions,
      meetingActions,
      meetingFollowUp
    );
    toast.success('PDF report generated');
  };

  const handleExportMarkdown = () => {
    const md = generateMeetingMarkdown(
      meeting,
      transcript || undefined,
      analysis || undefined,
      meetingDecisions,
      meetingActions,
      meetingFollowUp
    );
    const filename = `${meeting.title.replace(/[^a-zA-Z0-9_-]/g, '_')}_summary.md`;
    downloadBlob(md, filename, 'text/markdown;charset=utf-8');
    toast.success('Exported as Markdown');
  };

  const tabItems = [
    { id: 'overview', label: 'Overview', icon: <FileText className="w-4 h-4" /> },
    {
      id: 'transcript',
      label: 'Transcript',
      icon: <Clock className="w-4 h-4" />,
      badge: transcript?.text ? 'Ready' : undefined,
    },
    {
      id: 'insights',
      label: 'AI Insights',
      icon: <Sparkles className="w-4 h-4" />,
      badge: analysis ? 'Ready' : 'New',
    },
    {
      id: 'decisions',
      label: 'Decisions',
      icon: <CheckCircle2 className="w-4 h-4" />,
      badge: meetingDecisions.length,
    },
    {
      id: 'action-items',
      label: 'Action Items',
      icon: <ListTodo className="w-4 h-4" />,
      badge: meetingActions.length,
    },
    {
      id: 'follow-up',
      label: 'Follow-up Plan',
      icon: <Milestone className="w-4 h-4" />,
      badge: meetingFollowUp ? 'Active' : undefined,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Bar with Back CTA, Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <Button
            variant="ghost"
            size="sm"
            leftIcon={<ArrowLeft className="w-3.5 h-3.5" />}
            onClick={() => navigate('/meetings')}
            className="mb-1 -ml-2 text-content-secondary"
          >
            All Meetings
          </Button>

          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-content-primary dark:text-content-darkPrimary">
              {meeting.title}
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-surface-secondary dark:bg-surface-darkSecondary text-content-secondary border border-edge-light dark:border-edge-dark">
              {meeting.meetingType}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs text-content-secondary dark:text-content-darkSecondary pt-1">
            <span className="flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5" />
              {formatDateTime(meeting.meetingDate)}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {formatDuration(meeting.durationSeconds)}
            </span>
            {meeting.department && (
              <>
                <span>•</span>
                <span>{meeting.department}</span>
              </>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportPdf}
            leftIcon={<Download className="w-3.5 h-3.5" />}
          >
            Export PDF
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleExportMarkdown}
            leftIcon={<Share2 className="w-3.5 h-3.5" />}
          >
            Markdown
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsEditMetaOpen(true)}
            leftIcon={<Edit className="w-3.5 h-3.5" />}
          >
            Edit
          </Button>

          <button
            onClick={handleDeleteMeeting}
            className="p-2 rounded-xl text-content-secondary hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
            title="Delete meeting"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Tabs Bar */}
      <Tabs tabs={tabItems} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab 1: Overview */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="p-4 flex items-center gap-3.5">
              <div className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-content-secondary font-medium">Decisions Captured</p>
                <h4 className="text-xl font-bold text-content-primary dark:text-content-darkPrimary">
                  {meetingDecisions.length}
                </h4>
              </div>
            </Card>

            <Card className="p-4 flex items-center gap-3.5">
              <div className="p-2.5 rounded-xl bg-brand-light dark:bg-brand-primary/20 text-brand-primary dark:text-brand-secondary">
                <ListTodo className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-content-secondary font-medium">Action Items</p>
                <h4 className="text-xl font-bold text-content-primary dark:text-content-darkPrimary">
                  {meetingActions.length}
                </h4>
              </div>
            </Card>

            <Card className="p-4 flex items-center gap-3.5">
              <div className="p-2.5 rounded-xl bg-sky-50 dark:bg-sky-950/40 text-sky-600 dark:text-sky-400">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-content-secondary font-medium">AI Analysis</p>
                <h4 className="text-xl font-bold text-content-primary dark:text-content-darkPrimary capitalize">
                  {meeting.analysisStatus === 'completed' ? 'Verified' : 'Pending'}
                </h4>
              </div>
            </Card>
          </div>

          {/* Executive Summary Card */}
          <ExecutiveSummaryCard
            meeting={meeting}
            analysis={analysis || undefined}
            onAnalyze={handleTriggerAnalysis}
            isAnalyzing={isAnalyzing}
          />

          {/* Participants & Meeting Info */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Attendees & Spoken Participants</CardTitle>
                <CardDescription>Individuals contributing to this session</CardDescription>
              </CardHeader>
              <CardContent>
                {meeting.participants.length === 0 ? (
                  <p className="text-xs text-content-secondary">No attendees recorded.</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {meeting.participants.map((person, i) => (
                      <span
                        key={i}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-secondary dark:bg-surface-darkSecondary text-content-primary dark:text-content-darkPrimary text-xs font-medium border border-edge-light dark:border-edge-dark"
                      >
                        <Users className="w-3.5 h-3.5 text-content-secondary" />
                        {person}
                      </span>
                    ))}
                  </div>
                )}

                {meeting.description && (
                  <div className="mt-4 pt-3 border-t border-edge-light dark:border-edge-dark">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-content-secondary block mb-1">
                      Context / Notes
                    </span>
                    <p className="text-xs text-content-secondary leading-relaxed">
                      {meeting.description}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Audio & Inference Spec</CardTitle>
                <CardDescription>Technical transcription metadata</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2.5 text-xs text-content-secondary">
                <div className="flex justify-between py-1 border-b border-edge-light dark:border-edge-dark">
                  <span>Audio Binary:</span>
                  <span className="font-medium text-content-primary truncate max-w-[150px]">
                    {meeting.audioFilename || 'recorded_audio.mp3'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-edge-light dark:border-edge-dark">
                  <span>Engine:</span>
                  <span className="font-medium text-content-primary">OpenAI Whisper (Local)</span>
                </div>
                <div className="flex justify-between py-1 border-b border-edge-light dark:border-edge-dark">
                  <span>Analysis Model:</span>
                  <span className="font-medium text-content-primary">Groq Llama-3.3-70b</span>
                </div>
                <div className="flex justify-between py-1">
                  <span>Storage:</span>
                  <span className="font-medium text-content-primary">MongoDB Persistence</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Tab 2: Transcript */}
      {activeTab === 'transcript' && (
        <TranscriptEditor
          meeting={meeting}
          initialTranscript={transcript || undefined}
          onAnalysisRequested={handleTriggerAnalysis}
        />
      )}

      {/* Tab 3: AI Insights */}
      {activeTab === 'insights' && (
        <div className="space-y-6">
          <ExecutiveSummaryCard
            meeting={meeting}
            analysis={analysis || undefined}
            onAnalyze={handleTriggerAnalysis}
            isAnalyzing={isAnalyzing}
          />

          {analysis && (
            <>
              <KeyPointsSection
                keyPoints={analysis.keyPoints}
                topics={analysis.topics}
              />
              <RisksAndQuestions
                risks={analysis.risks}
                openQuestions={analysis.openQuestions}
                suggestedNextSteps={analysis.suggestedNextSteps}
                meetingId={meeting.id}
                meetingTitle={meeting.title}
              />
            </>
          )}
        </div>
      )}

      {/* Tab 4: Decisions */}
      {activeTab === 'decisions' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-content-primary dark:text-content-darkPrimary">
              Decisions Captured ({meetingDecisions.length})
            </h3>
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Plus className="w-3.5 h-3.5" />}
              onClick={() => {
                setSelectedDecision(null);
                setIsDecisionModalOpen(true);
              }}
            >
              Add Decision
            </Button>
          </div>

          {meetingDecisions.length === 0 ? (
            <Card className="p-8 text-center text-xs text-content-secondary">
              No decisions recorded for this meeting. You can add one manually or run AI analysis.
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {meetingDecisions.map((d) => (
                <DecisionCard
                  key={d.id}
                  decision={d}
                  onEdit={(dec) => {
                    setSelectedDecision(dec);
                    setIsDecisionModalOpen(true);
                  }}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 5: Action Items */}
      {activeTab === 'action-items' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-content-primary dark:text-content-darkPrimary">
              Meeting Action Items ({meetingActions.length})
            </h3>
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Plus className="w-3.5 h-3.5" />}
              onClick={() => {
                setSelectedAction(null);
                setIsActionModalOpen(true);
              }}
            >
              Add Action Item
            </Button>
          </div>

          <ActionItemList
            tasks={meetingActions}
            onEdit={(task) => {
              setSelectedAction(task);
              setIsActionModalOpen(true);
            }}
          />
        </div>
      )}

      {/* Tab 6: Follow-up Plan */}
      {activeTab === 'follow-up' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-content-primary dark:text-content-darkPrimary">
              Follow-up Execution Plan
            </h3>
            {!meetingFollowUp ? (
              <Button
                variant="primary"
                size="sm"
                leftIcon={<Sparkles className="w-3.5 h-3.5" />}
                onClick={() => generateFollowUpPlan(meeting.id)}
              >
                Generate Follow-up Plan
              </Button>
            ) : (
              <Button
                variant="outline"
                size="sm"
                leftIcon={<Plus className="w-3.5 h-3.5" />}
                onClick={() => {
                  setSelectedPlan(null);
                  setIsFollowUpModalOpen(true);
                }}
              >
                New Plan
              </Button>
            )}
          </div>

          {meetingFollowUp ? (
            <FollowUpTimeline
              plan={meetingFollowUp}
              onEdit={(plan) => {
                setSelectedPlan(plan);
                setIsFollowUpModalOpen(true);
              }}
            />
          ) : (
            <Card className="p-8 text-center text-xs text-content-secondary space-y-3">
              <p>No follow-up plan created yet for this meeting.</p>
              <Button
                variant="primary"
                size="sm"
                leftIcon={<Sparkles className="w-3.5 h-3.5" />}
                onClick={() => generateFollowUpPlan(meeting.id)}
              >
                Generate Plan via AI
              </Button>
            </Card>
          )}
        </div>
      )}

      {/* Edit Metadata Modal */}
      <Modal
        isOpen={isEditMetaOpen}
        onClose={() => setIsEditMetaOpen(false)}
        title="Edit Meeting Metadata"
        description="Update meeting title, type, and contextual notes"
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsEditMetaOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleSaveMeta}>
              Save Changes
            </Button>
          </>
        }
      >
        <form onSubmit={handleSaveMeta} className="space-y-4">
          <Input
            label="Meeting Title"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
          />

          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Meeting Type"
              value={editType}
              onChange={(e) => setEditType(e.target.value)}
            >
              {MEETING_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </Select>

            <Input
              label="Department"
              value={editDept}
              onChange={(e) => setEditDept(e.target.value)}
            />
          </div>

          <Textarea
            label="Context & Notes"
            rows={3}
            value={editDesc}
            onChange={(e) => setEditDesc(e.target.value)}
          />
        </form>
      </Modal>

      {/* Decision Form Modal */}
      <DecisionFormModal
        isOpen={isDecisionModalOpen}
        onClose={() => setIsDecisionModalOpen(false)}
        decision={selectedDecision}
        defaultMeetingId={meeting.id}
      />

      {/* Action Item Form Modal */}
      <ActionItemFormModal
        isOpen={isActionModalOpen}
        onClose={() => setIsActionModalOpen(false)}
        task={selectedAction}
        defaultMeetingId={meeting.id}
      />

      {/* Follow-up Plan Form Modal */}
      <FollowUpFormModal
        isOpen={isFollowUpModalOpen}
        onClose={() => setIsFollowUpModalOpen(false)}
        plan={selectedPlan}
        defaultMeetingId={meeting.id}
      />
    </div>
  );
};
