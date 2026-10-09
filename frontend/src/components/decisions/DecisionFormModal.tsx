import React, { useState, useEffect } from 'react';
import { Decision, DecisionStatus } from '../../types';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input, Textarea, Select } from '../ui/Input';
import { useData } from '../../context/DataContext';

interface DecisionFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  decision?: Decision | null;
  defaultMeetingId?: string;
}

export const DecisionFormModal: React.FC<DecisionFormModalProps> = ({
  isOpen,
  onClose,
  decision,
  defaultMeetingId,
}) => {
  const { createDecision, updateDecision, meetings } = useData();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [owner, setOwner] = useState('');
  const [status, setStatus] = useState<DecisionStatus>('Confirmed');
  const [category, setCategory] = useState('Strategy');
  const [meetingId, setMeetingId] = useState(defaultMeetingId || '');
  const [evidence, setEvidence] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (decision) {
      setTitle(decision.title);
      setDescription(decision.description);
      setOwner(decision.owner || '');
      setStatus(decision.status);
      setCategory(decision.category || 'Strategy');
      setMeetingId(decision.meetingId);
      setEvidence(decision.evidence || '');
    } else {
      setTitle('');
      setDescription('');
      setOwner('');
      setStatus('Confirmed');
      setCategory('Strategy');
      setMeetingId(defaultMeetingId || (meetings[0]?.id ?? ''));
      setEvidence('');
    }
  }, [decision, defaultMeetingId, meetings, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setIsSubmitting(true);
    try {
      const selectedMeeting = meetings.find((m) => m.id === meetingId);

      if (decision) {
        await updateDecision(decision.id, {
          title: title.trim(),
          description: description.trim(),
          owner: owner.trim() || undefined,
          status,
          category: category.trim(),
          meetingId,
          meetingTitle: selectedMeeting?.title,
          evidence: evidence.trim() || undefined,
        });
      } else {
        await createDecision({
          title: title.trim(),
          description: description.trim(),
          owner: owner.trim() || undefined,
          status,
          category: category.trim(),
          meetingId: meetingId || 'general',
          meetingTitle: selectedMeeting?.title || 'General Decision',
          evidence: evidence.trim() || undefined,
          isManual: true,
        });
      }
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={decision ? 'Edit Decision' : 'Record New Decision'}
      description="Document executive commitments and strategic agreements with context"
      maxWidth="md"
      footer={
        <>
          <Button variant="outline" size="sm" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            isLoading={isSubmitting}
            onClick={handleSubmit}
          >
            {decision ? 'Update Decision' : 'Save Decision'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Decision Title *"
          required
          placeholder="e.g. Enforce v1 API feature freeze by Oct 20"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />

        <div className="grid grid-cols-2 gap-4">
          <Select
            label="Decision Status"
            value={status}
            onChange={(e) => setStatus(e.target.value as DecisionStatus)}
          >
            <option value="Confirmed">Confirmed</option>
            <option value="Proposed">Proposed</option>
            <option value="Rejected">Rejected</option>
            <option value="Superseded">Superseded</option>
          </Select>

          <Input
            label="Category"
            placeholder="e.g. Architecture, Strategy"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Decision Owner / Sponsor"
            placeholder="e.g. Elena Rostova"
            value={owner}
            onChange={(e) => setOwner(e.target.value)}
          />

          <Select
            label="Related Meeting"
            value={meetingId}
            onChange={(e) => setMeetingId(e.target.value)}
          >
            <option value="general">No Meeting (Standalone)</option>
            {meetings.map((m) => (
              <option key={m.id} value={m.id}>
                {m.title}
              </option>
            ))}
          </Select>
        </div>

        <Textarea
          label="Detailed Description"
          rows={3}
          placeholder="Elaborate on what was agreed upon and the underlying rationale..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />

        <Textarea
          label="Transcript Context / Evidence (Optional)"
          rows={2}
          placeholder="Relevant spoken quote from transcript supporting this decision..."
          value={evidence}
          onChange={(e) => setEvidence(e.target.value)}
        />
      </form>
    </Modal>
  );
};
