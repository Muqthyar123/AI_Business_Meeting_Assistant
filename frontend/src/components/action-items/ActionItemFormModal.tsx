import React, { useState, useEffect } from 'react';
import { ActionItem, PriorityLevel, TaskStatus } from '../../types';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input, Textarea, Select } from '../ui/Input';
import { useData } from '../../context/DataContext';

interface ActionItemFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  task?: ActionItem | null;
  defaultMeetingId?: string;
}

export const ActionItemFormModal: React.FC<ActionItemFormModalProps> = ({
  isOpen,
  onClose,
  task,
  defaultMeetingId,
}) => {
  const { createActionItem, updateActionItem, meetings } = useData();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [assignee, setAssignee] = useState('');
  const [assigneeEmail, setAssigneeEmail] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [priority, setPriority] = useState<PriorityLevel>('Medium');
  const [status, setStatus] = useState<TaskStatus>('To Do');
  const [meetingId, setMeetingId] = useState(defaultMeetingId || '');
  const [evidence, setEvidence] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (task) {
      setTitle(task.title);
      setDescription(task.description || '');
      setAssignee(task.assignee || '');
      setAssigneeEmail(task.assigneeEmail || '');
      setDueDate(task.dueDate ? task.dueDate.split('T')[0] : '');
      setPriority(task.priority);
      setStatus(task.status);
      setMeetingId(task.meetingId);
      setEvidence(task.evidence || '');
    } else {
      setTitle('');
      setDescription('');
      setAssignee('');
      setAssigneeEmail('');
      setDueDate('');
      setPriority('Medium');
      setStatus('To Do');
      setMeetingId(defaultMeetingId || (meetings[0]?.id ?? ''));
      setEvidence('');
    }
  }, [task, defaultMeetingId, meetings, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setIsSubmitting(true);
    try {
      const selectedMeeting = meetings.find((m) => m.id === meetingId);

      if (task) {
        await updateActionItem(task.id, {
          title: title.trim(),
          description: description.trim() || undefined,
          assignee: assignee.trim() || undefined,
          assigneeEmail: assigneeEmail.trim() || undefined,
          dueDate: dueDate ? new Date(dueDate).toISOString() : undefined,
          priority,
          status,
          meetingId,
          meetingTitle: selectedMeeting?.title,
          evidence: evidence.trim() || undefined,
        });
      } else {
        await createActionItem({
          title: title.trim(),
          description: description.trim() || undefined,
          assignee: assignee.trim() || undefined,
          assigneeEmail: assigneeEmail.trim() || undefined,
          dueDate: dueDate ? new Date(dueDate).toISOString() : undefined,
          priority,
          status,
          meetingId: meetingId || 'general',
          meetingTitle: selectedMeeting?.title || 'General Task',
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
      title={task ? 'Edit Action Item' : 'Create New Action Item'}
      description="Assign accountability and track deadlines from meetings"
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
            {task ? 'Update Task' : 'Create Task'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Task Title *"
          required
          placeholder="e.g. Finalize OpenAPI 3.1 specification"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />

        <div className="grid grid-cols-2 gap-4">
          <Select
            label="Priority"
            value={priority}
            onChange={(e) => setPriority(e.target.value as PriorityLevel)}
          >
            <option value="Urgent">Urgent</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </Select>

          <Select
            label="Status"
            value={status}
            onChange={(e) => setStatus(e.target.value as TaskStatus)}
          >
            <option value="To Do">To Do</option>
            <option value="In Progress">In Progress</option>
            <option value="Blocked">Blocked</option>
            <option value="Completed">Completed</option>
            <option value="Cancelled">Cancelled</option>
          </Select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Assignee Name"
            placeholder="e.g. David Chen"
            value={assignee}
            onChange={(e) => setAssignee(e.target.value)}
          />

          <Input
            label="Due Date"
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Assignee Email (Optional)"
            type="email"
            placeholder="david.chen@meetmind.ai"
            value={assigneeEmail}
            onChange={(e) => setAssigneeEmail(e.target.value)}
          />

          <Select
            label="Source Meeting"
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
          placeholder="Outline deliverables, sub-tasks, or expectations..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />

        <Textarea
          label="Transcript Evidence Excerpt"
          rows={2}
          placeholder="Quotation from meeting audio supporting this action..."
          value={evidence}
          onChange={(e) => setEvidence(e.target.value)}
        />
      </form>
    </Modal>
  );
};
