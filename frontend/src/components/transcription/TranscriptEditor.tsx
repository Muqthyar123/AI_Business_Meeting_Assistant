import React, { useState, useEffect, useMemo } from 'react';
import {
  Save,
  RotateCcw,
  Copy,
  Download,
  Search,
  Check,
  FileText,
  Clock,
  Sparkles,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { Meeting, Transcript, TranscriptSegment } from '../../types';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { formatDateTime, formatDuration, formatTimestamp } from '../../utils/formatters';
import { exportAsTxt } from '../../utils/exportHelpers';
import { useData } from '../../context/DataContext';
import { toast } from 'sonner';

interface TranscriptEditorProps {
  meeting: Meeting;
  initialTranscript?: Transcript;
  onAnalysisRequested?: () => void;
}

export const TranscriptEditor: React.FC<TranscriptEditorProps> = ({
  meeting,
  initialTranscript,
  onAnalysisRequested,
}) => {
  const { saveTranscript } = useData();

  const [text, setText] = useState(initialTranscript?.text || '');
  const [originalText, setOriginalText] = useState(initialTranscript?.text || '');
  const [isSaving, setIsSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeView, setActiveView] = useState<'editor' | 'segments'>('editor');
  const [lastSavedTime, setLastSavedTime] = useState<string | null>(null);

  useEffect(() => {
    if (initialTranscript?.text) {
      setText(initialTranscript.text);
      setOriginalText(initialTranscript.text);
    }
  }, [initialTranscript]);

  const hasUnsavedChanges = text !== originalText;

  // Word and character count
  const wordCount = useMemo(() => {
    return text.trim() ? text.trim().split(/\s+/).length : 0;
  }, [text]);

  const charCount = text.length;

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await saveTranscript(meeting.id, { text });
      setOriginalText(text);
      setLastSavedTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    } catch (err: any) {
      toast.error(`Failed to save transcript: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDiscard = () => {
    if (window.confirm('Discard unsaved edits to this transcript?')) {
      setText(originalText);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success('Transcript copied to clipboard');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadTxt = () => {
    const filename = `${meeting.title.replace(/[^a-zA-Z0-9_-]/g, '_')}_transcript.txt`;
    exportAsTxt(text, filename);
    toast.success('Transcript downloaded as TXT');
  };

  const searchMatchCount = useMemo(() => {
    if (!searchQuery.trim()) return 0;
    try {
      const regex = new RegExp(searchQuery.trim(), 'gi');
      return (text.match(regex) || []).length;
    } catch {
      return 0;
    }
  }, [searchQuery, text]);

  const segments = initialTranscript?.segments || [];

  return (
    <div className="space-y-4">
      {/* Transcript Header Stats Bar */}
      <Card className="p-4 sm:p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3 text-xs text-content-secondary dark:text-content-darkSecondary">
            <span className="font-semibold text-content-primary dark:text-content-darkPrimary">
              {initialTranscript?.filename || meeting.audioFilename || 'Audio Recording'}
            </span>
            <span>•</span>
            <span className="inline-flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {formatDuration(initialTranscript?.durationSeconds || meeting.durationSeconds)}
            </span>
            <span>•</span>
            <span>Lang: {initialTranscript?.language || 'English'}</span>
            <span>•</span>
            <span>{wordCount.toLocaleString()} words</span>
            <span>•</span>
            <span>{charCount.toLocaleString()} chars</span>

            {lastSavedTime && (
              <>
                <span>•</span>
                <span className="text-emerald-600 dark:text-emerald-400">
                  Saved at {lastSavedTime}
                </span>
              </>
            )}

            {hasUnsavedChanges && (
              <Badge variant="warning" size="sm" dot>
                Unsaved edits
              </Badge>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            {segments.length > 0 && (
              <div className="flex rounded-lg border border-edge-light dark:border-edge-dark p-0.5 bg-surface-secondary/40">
                <button
                  type="button"
                  onClick={() => setActiveView('editor')}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                    activeView === 'editor'
                      ? 'bg-white dark:bg-surface-darkSecondary text-brand-primary shadow-xs'
                      : 'text-content-secondary hover:text-content-primary'
                  }`}
                >
                  Text Editor
                </button>
                <button
                  type="button"
                  onClick={() => setActiveView('segments')}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                    activeView === 'segments'
                      ? 'bg-white dark:bg-surface-darkSecondary text-brand-primary shadow-xs'
                      : 'text-content-secondary hover:text-content-primary'
                  }`}
                >
                  Timestamped Segments ({segments.length})
                </button>
              </div>
            )}

            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              leftIcon={copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              title="Copy full text"
            >
              {copied ? 'Copied' : 'Copy'}
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadTxt}
              leftIcon={<Download className="w-3.5 h-3.5" />}
              title="Download text file"
            >
              Export TXT
            </Button>

            {hasUnsavedChanges && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleDiscard}
                  leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
                >
                  Discard
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  isLoading={isSaving}
                  onClick={handleSave}
                  leftIcon={<Save className="w-3.5 h-3.5" />}
                >
                  Save Changes
                </Button>
              </>
            )}
          </div>
        </div>

        {/* In-Transcript Search Bar */}
        <div className="mt-4 pt-3 border-t border-edge-light dark:border-edge-dark flex items-center justify-between gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-content-secondary absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search words within transcript..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-edge-light dark:border-edge-dark bg-surface-secondary/40 text-xs text-content-primary focus:outline-none focus:border-brand-primary"
            />
          </div>
          {searchQuery && (
            <span className="text-xs text-content-secondary shrink-0">
              {searchMatchCount} match{searchMatchCount === 1 ? '' : 'es'} found
            </span>
          )}
        </div>
      </Card>

      {/* Editor Body */}
      {activeView === 'editor' ? (
        <Card className="overflow-hidden">
          <div className="p-4 sm:p-6 bg-white dark:bg-surface-darkCard">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Transcript text will appear here..."
              rows={18}
              className="w-full bg-transparent text-sm sm:text-base leading-relaxed text-content-primary dark:text-content-darkPrimary font-sans focus:outline-none resize-y selection:bg-brand-light selection:text-brand-primary"
              style={{ minHeight: '380px' }}
            />
          </div>
          <div className="px-6 py-3 border-t border-edge-light dark:border-edge-dark bg-surface-secondary/40 dark:bg-surface-darkSecondary/30 flex items-center justify-between text-xs text-content-secondary">
            <span>Tip: You can edit or clarify words before requesting AI analysis.</span>
            {hasUnsavedChanges && (
              <span className="text-amber-600 dark:text-amber-400 font-semibold">
                * Unsaved changes
              </span>
            )}
          </div>
        </Card>
      ) : (
        /* Timestamped Segments View */
        <Card className="p-4 sm:p-6 space-y-3">
          {segments.map((seg) => {
            const isMatch =
              searchQuery.trim() &&
              seg.text.toLowerCase().includes(searchQuery.trim().toLowerCase());

            return (
              <div
                key={seg.id}
                className={`p-3.5 rounded-xl border transition-all ${
                  isMatch
                    ? 'border-brand-primary bg-brand-light/30 dark:bg-brand-primary/10'
                    : 'border-edge-light dark:border-edge-dark bg-surface-secondary/30 dark:bg-surface-darkSecondary/30 hover:border-slate-300'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-semibold text-brand-primary dark:text-brand-secondary">
                    {seg.speaker || 'Speaker'}
                  </span>
                  <span className="text-[11px] font-mono text-content-secondary bg-surface-secondary dark:bg-surface-darkSecondary px-2 py-0.5 rounded border border-edge-light dark:border-edge-dark">
                    {formatTimestamp(seg.start)} - {formatTimestamp(seg.end)}
                  </span>
                </div>
                <p className="text-sm text-content-primary dark:text-content-darkPrimary leading-relaxed">
                  {seg.text}
                </p>
              </div>
            );
          })}
        </Card>
      )}
    </div>
  );
};
