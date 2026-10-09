import React, { useState, useEffect } from 'react';
import { FollowUpPlan, FollowUpStep, FollowUpStatus } from '../../types';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input, Textarea, Select } from '../ui/Input';
import { Plus, Trash2 } from 'lucide-react';
import { useData } from '../../context/DataContext';

interface FollowUpFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  plan?: FollowUpPlan | null;
  defaultMeetingId?: string;
}

export const FollowUpFormModal: React.FC<FollowUpFormModalProps> = ({
  isOpen,
  onClose,
  plan,
  defaultMeetingId,
}) => {
  const { saveFollowUp, meetings } = useData();

  const [title, setTitle] = useState('');
  const [objective, setObjective] = useState('');
  const [status, setStatus] = useState<FollowUpStatus>('Active');
  const [meetingId, setMeetingId] = useState(defaultMeetingId || '');
  const [steps, setSteps] = useState<FollowUpStep[]>([
    { id: 'st-1', stepNumber: 1, title: '', suggestedTiming: '', owner: '', status: 'pending' },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (plan) {
      setTitle(plan.title);
      setObjective(plan.objective);
      setStatus(plan.status);
      setMeetingId(plan.meetingId);
      setSteps(plan.steps.length > 0 ? plan.steps : [
        { id: 'st-1', stepNumber: 1, title: '', suggestedTiming: '', owner: '', status: 'pending' }
      ]);
    } else {
      setTitle('');
      setObjective('');
      setStatus('Active');
      setMeetingId(defaultMeetingId || (meetings[0]?.id ?? ''));
      setSteps([
        { id: 'st-1', stepNumber: 1, title: '', suggestedTiming: '', owner: '', status: 'pending' }
      ]);
    }
  }, [plan, defaultMeetingId, meetings, isOpen]);

  const addStep = () => {
    setSteps((prev) => [
      ...prev,
      {
        id: `st-${Date.now()}`,
        stepNumber: prev.length + 1,
        title: '',
        suggestedTiming: '',
        owner: '',
        status: 'pending',
      },
    ]);
  };

  const removeStep = (index: number) => {
    setSteps((prev) =>
      prev
        .filter((_, i) => i !== index)
        .map((s, idx) => ({ ...s, stepNumber: idx + 1 }))
    );
  };

  const updateStepField = (index: number, field: keyof FollowUpStep, val: any) => {
    setSteps((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], [field]: val };
      return copy;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !objective.trim()) return;

    setIsSubmitting(true);
    try {
      const selectedMeeting = meetings.find((m) => m.id === meetingId);
      const validSteps = steps.filter((s) => s.title.trim().length > 0);

      await saveFollowUp({
        id: plan?.id,
        meetingId: meetingId || 'general',
        meetingTitle: selectedMeeting?.title || 'General Execution',
        title: title.trim(),
        objective: objective.trim(),
        status,
        steps: validSteps,
      });

      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={plan ? 'Edit Follow-up Plan' : 'Create Follow-up Plan'}
      description="Structure multi-step action sequences from executive sessions"
      maxWidth="xl"
      footer={
        <>
          <Button variant="outline" size="sm" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button variant="primary" size="sm" isLoading={isSubmitting} onClick={handleSubmit}>
            {plan ? 'Update Plan' : 'Save Plan'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Plan Title *"
          required
          placeholder="e.g. Q4 Transition & Engineering Hardening Plan"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />

        <div className="grid grid-cols-2 gap-4">
          <Select
            label="Related Meeting"
            value={meetingId}
            onChange={(e) => setMeetingId(e.target.value)}
          >
            <option value="general">No Meeting (General)</option>
            {meetings.map((m) => (
              <option key={m.id} value={m.id}>
                {m.title}
              </option>
            ))}
          </Select>

          <Select
            label="Plan Status"
            value={status}
            onChange={(e) => setStatus(e.target.value as FollowUpStatus)}
          >
            <option value="Active">Active</option>
            <option value="Draft">Draft</option>
            <option value="Completed">Completed</option>
            <option value="Archived">Archived</option>
          </Select>
        </div>

        <Textarea
          label="Strategic Objective *"
          required
          rows={2}
          placeholder="High-level goal and desired outcomes..."
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
        />

        {/* Steps Editor */}
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold uppercase tracking-wider text-content-secondary">
              Ordered Milestones ({steps.length})
            </label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addStep}
              leftIcon={<Plus className="w-3.5 h-3.5" />}
            >
              Add Step
            </Button>
          </div>

          <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
            {steps.map((step, idx) => (
              <div
                key={step.id}
                className="p-3 rounded-xl border border-edge-light dark:border-edge-dark bg-surface-secondary/30 dark:bg-surface-darkSecondary/30 flex items-start gap-2.5"
              >
                <span className="w-5 h-5 rounded-full bg-brand-light dark:bg-brand-primary/20 text-brand-primary text-xs font-bold flex items-center justify-center shrink-0 mt-2">
                  {idx + 1}
                </span>

                <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <div className="sm:col-span-3">
                    <input
                      type="text"
                      placeholder="Milestone title..."
                      value={step.title}
                      onChange={(e) => updateStepField(idx, 'title', e.target.value)}
                      className="w-full text-xs font-medium px-2.5 py-1.5 rounded-lg border border-edge-light dark:border-edge-dark bg-white dark:bg-surface-darkCard focus:outline-none focus:border-brand-primary"
                    />
                  </div>
                  <div>
                    <input
                      type="text"
                      placeholder="Timing (e.g. By Oct 15)..."
                      value={step.suggestedTiming || ''}
                      onChange={(e) => updateStepField(idx, 'suggestedTiming', e.target.value)}
                      className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-edge-light dark:border-edge-dark bg-white dark:bg-surface-darkCard focus:outline-none focus:border-brand-primary"
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <input
                      type="text"
                      placeholder="Owner (e.g. Sarah Jenkins)..."
                      value={step.owner || ''}
                      onChange={(e) => updateStepField(idx, 'owner', e.target.value)}
                      className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-edge-light dark:border-edge-dark bg-white dark:bg-surface-darkCard focus:outline-none focus:border-brand-primary"
                    />
                  </div>
                </div>

                {steps.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeStep(idx)}
                    className="p-1.5 text-content-secondary hover:text-rose-600 transition-colors mt-1"
                    title="Remove step"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </form>
    </Modal>
  );
};
