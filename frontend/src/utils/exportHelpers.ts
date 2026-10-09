import { jsPDF } from 'jspdf';
import { Meeting, Transcript, Analysis, Decision, ActionItem, FollowUpPlan } from '../types';
import { formatDate, formatDuration } from './formatters';

export function downloadBlob(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function exportAsTxt(text: string, filename = 'meeting-transcript.txt') {
  downloadBlob(text, filename, 'text/plain;charset=utf-8');
}

export function exportAsJson(data: any, filename = 'meeting-data.json') {
  const jsonStr = JSON.stringify(data, null, 2);
  downloadBlob(jsonStr, filename, 'application/json;charset=utf-8');
}

export function exportAsCsv(rows: Record<string, any>[], filename = 'export.csv') {
  if (rows.length === 0) return;
  const headers = Object.keys(rows[0]);
  const csvLines = [
    headers.join(','),
    ...rows.map((row) =>
      headers
        .map((h) => {
          const val = row[h] === undefined || row[h] === null ? '' : String(row[h]);
          return `"${val.replace(/"/g, '""')}"`;
        })
        .join(',')
    ),
  ];
  downloadBlob(csvLines.join('\n'), filename, 'text/csv;charset=utf-8');
}

export function exportDecisionsCsv(decisions: Decision[], filename = 'decisions.csv') {
  const rows = decisions.map((d) => ({
    Title: d.title,
    Status: d.status,
    Owner: d.owner || 'Unassigned',
    Meeting: d.meetingTitle || d.meetingId,
    Description: d.description,
    Evidence: d.evidence || '',
    Created: formatDate(d.createdAt),
  }));
  exportAsCsv(rows, filename);
}

export function exportActionItemsCsv(tasks: ActionItem[], filename = 'action-items.csv') {
  const rows = tasks.map((t) => ({
    Title: t.title,
    Status: t.status,
    Priority: t.priority,
    Assignee: t.assignee || 'Unassigned',
    DueDate: t.dueDate ? formatDate(t.dueDate) : 'No deadline',
    Meeting: t.meetingTitle || t.meetingId,
    Description: t.description || '',
    Evidence: t.evidence || '',
  }));
  exportAsCsv(rows, filename);
}

export function generateMeetingMarkdown(
  meeting: Meeting,
  transcript?: Transcript,
  analysis?: Analysis,
  decisions?: Decision[],
  actions?: ActionItem[],
  followUp?: FollowUpPlan
): string {
  let md = `# ${meeting.title}\n\n`;
  md += `**Date:** ${formatDate(meeting.meetingDate)}\n`;
  md += `**Type:** ${meeting.meetingType}\n`;
  md += `**Duration:** ${formatDuration(meeting.durationSeconds)}\n`;
  md += `**Participants:** ${meeting.participants.join(', ') || 'None recorded'}\n\n`;

  if (analysis?.summary) {
    md += `## Executive Summary\n${analysis.summary}\n\n`;
  }

  if (analysis?.keyPoints && analysis.keyPoints.length > 0) {
    md += `## Key Discussion Points\n`;
    analysis.keyPoints.forEach((point) => {
      md += `- ${point}\n`;
    });
    md += `\n`;
  }

  if (decisions && decisions.length > 0) {
    md += `## Extracted Decisions\n`;
    decisions.forEach((d) => {
      md += `### ${d.title} [${d.status}]\n`;
      md += `${d.description}\n`;
      if (d.owner) md += `- **Owner:** ${d.owner}\n`;
      if (d.evidence) md += `- **Context:** *"${d.evidence}"*\n`;
      md += `\n`;
    });
  }

  if (actions && actions.length > 0) {
    md += `## Action Items\n`;
    actions.forEach((a) => {
      md += `- [${a.status === 'Completed' ? 'x' : ' '}] **${a.title}** (${a.priority} Priority)\n`;
      md += `  - **Assignee:** ${a.assignee || 'Unassigned'}\n`;
      md += `  - **Due:** ${a.dueDate ? formatDate(a.dueDate) : 'No deadline'}\n`;
      if (a.description) md += `  - ${a.description}\n`;
      if (a.evidence) md += `  - *Context: "${a.evidence}"*\n`;
    });
    md += `\n`;
  }

  if (followUp?.steps && followUp.steps.length > 0) {
    md += `## Follow-up Plan: ${followUp.title}\n`;
    md += `**Objective:** ${followUp.objective}\n\n`;
    followUp.steps.forEach((step) => {
      md += `${step.stepNumber}. **${step.title}** ${step.suggestedTiming ? `(${step.suggestedTiming})` : ''}\n`;
      if (step.description) md += `   ${step.description}\n`;
    });
    md += `\n`;
  }

  if (transcript?.text) {
    md += `## Full Transcript\n\n${transcript.text}\n`;
  }

  return md;
}

export function exportMeetingAsPdf(
  meeting: Meeting,
  analysis?: Analysis,
  decisions?: Decision[],
  actions?: ActionItem[],
  followUp?: FollowUpPlan
) {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'pt',
    format: 'a4',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  let y = 40;

  // Header banner
  doc.setFillColor(101, 88, 232); // #6558E8
  doc.rect(0, 0, pageWidth, 55, 'F');

  doc.setTextColor(255, 255, 255);
  doc.setFontSize(18);
  doc.setFont('helvetica', 'bold');
  doc.text('MeetMind — Executive Meeting Report', 40, 35);

  y = 80;
  doc.setTextColor(32, 34, 56);
  doc.setFontSize(16);
  doc.text(meeting.title, 40, y);

  y += 20;
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(115, 118, 140);
  doc.text(
    `Date: ${formatDate(meeting.meetingDate)}  |  Type: ${meeting.meetingType}  |  Duration: ${formatDuration(
      meeting.durationSeconds
    )}`,
    40,
    y
  );

  y += 15;
  doc.text(`Participants: ${meeting.participants.join(', ') || 'N/A'}`, 40, y);

  y += 25;
  doc.setDrawColor(229, 231, 240);
  doc.line(40, y, pageWidth - 40, y);
  y += 20;

  // Helper to add multiline text with page break handling
  function addSection(title: string, content: string[]) {
    if (y > 720) {
      doc.addPage();
      y = 40;
    }
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(101, 88, 232);
    doc.text(title, 40, y);
    y += 18;

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(32, 34, 56);

    content.forEach((line) => {
      const splitLines = doc.splitTextToSize(line, pageWidth - 80);
      splitLines.forEach((l: string) => {
        if (y > 760) {
          doc.addPage();
          y = 40;
        }
        doc.text(l, 40, y);
        y += 14;
      });
      y += 4;
    });
    y += 15;
  }

  if (analysis?.summary) {
    addSection('Executive Summary', [analysis.summary]);
  }

  if (analysis?.keyPoints && analysis.keyPoints.length > 0) {
    addSection(
      'Key Discussion Points',
      analysis.keyPoints.map((p) => `• ${p}`)
    );
  }

  if (decisions && decisions.length > 0) {
    addSection(
      'Decisions Captured',
      decisions.map(
        (d) => `• [${d.status}] ${d.title}${d.owner ? ` (Owner: ${d.owner})` : ''} - ${d.description}`
      )
    );
  }

  if (actions && actions.length > 0) {
    addSection(
      'Action Items',
      actions.map(
        (a) =>
          `• [${a.status}] ${a.title} - Assignee: ${a.assignee || 'Unassigned'} | Due: ${
            a.dueDate ? formatDate(a.dueDate) : 'No date'
          } | Priority: ${a.priority}`
      )
    );
  }

  if (followUp?.steps && followUp.steps.length > 0) {
    addSection(
      `Follow-up Plan: ${followUp.title}`,
      followUp.steps.map(
        (s) => `${s.stepNumber}. ${s.title}${s.suggestedTiming ? ` (${s.suggestedTiming})` : ''}: ${s.description || ''}`
      )
    );
  }

  const cleanTitle = meeting.title.replace(/[^a-zA-Z0-9_-]/g, '_').substring(0, 30);
  doc.save(`${cleanTitle}_report.pdf`);
}
