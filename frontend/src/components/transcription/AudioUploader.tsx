import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UploadCloud,
  FileAudio,
  FileText,
  FileSpreadsheet,
  X,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  Cpu,
  Sparkles,
  ClipboardPaste,
  FileType,
  Radio,
  Mic,
  Copy,
  Check,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input, Textarea, Select } from '../ui/Input';
import {
  MEETING_TYPES,
  TRANSCRIPTION_LANGUAGES,
  WHISPER_MODELS,
  SUPPORTED_EXTENSIONS,
  MAX_FILE_SIZE_BYTES,
  MAX_FILE_SIZE_LABEL,
} from '../../config/constants';
import { formatFileSize } from '../../utils/formatters';
import { useData } from '../../context/DataContext';
import { liveStreamClient, LiveStreamSegment } from '../../services/liveStream';
import { toast } from 'sonner';

export const AudioUploader: React.FC = () => {
  const navigate = useNavigate();
  const { uploadAudioFile, createMeeting, triggerAnalysis } = useData();

  // Mode: file upload vs manual transcript entry
  const [entryMode, setEntryMode] = useState<'upload' | 'manual'>('upload');

  // Form State
  const [title, setTitle] = useState('');
  const [meetingDate, setMeetingDate] = useState(() => {
    const now = new Date();
    return new Date(now.getTime() - now.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);
  });
  const [meetingType, setMeetingType] = useState('Team Meeting');
  const [department, setDepartment] = useState('Product & Engineering');
  const [participantsInput, setParticipantsInput] = useState('');
  const [description, setDescription] = useState('');
  const [language, setLanguage] = useState('auto');
  const [model, setModel] = useState('base');

  // Manual Transcript State
  const [manualTranscript, setManualTranscript] = useState('');
  const [hasCopied, setHasCopied] = useState(false);

  // Live WebSocket Stream State
  const [isLiveConnected, setIsLiveConnected] = useState(false);
  const [lastLiveTimestamp, setLastLiveTimestamp] = useState<string | null>(null);
  const [liveSegmentCount, setLiveSegmentCount] = useState(0);

  // File Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatusText, setUploadStatusText] = useState('');

  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Subscribe to live WebSocket speech streaming from Desktop Assistant
  useEffect(() => {
    const unsubscribe = liveStreamClient.subscribe(
      (segment: LiveStreamSegment) => {
        if (!segment.text || !segment.text.trim()) return;
        const incomingText = segment.text.trim();

        // Switch automatically to the manual transcript entry tab
        setEntryMode('manual');
        setLastLiveTimestamp(segment.timestamp || new Date().toLocaleTimeString());
        setLiveSegmentCount((prev) => prev + 1);

        // Append seamlessly without overwriting
        setManualTranscript((prev) => {
          if (!prev || !prev.trim()) {
            return incomingText;
          }
          const cleanPrev = prev.trim();
          const lastChar = cleanPrev[cleanPrev.length - 1];
          if ('.!?'.includes(lastChar)) {
            return `${cleanPrev} ${incomingText}`;
          } else if (',;:'.includes(lastChar)) {
            return `${cleanPrev} ${incomingText}`;
          } else {
            return `${cleanPrev}. ${incomingText}`;
          }
        });

        // Set default title if empty
        setTitle((prevTitle) => {
          if (!prevTitle || !prevTitle.trim()) {
            return `Live Meeting Session - ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
          }
          return prevTitle;
        });

        // Scroll textarea to bottom
        setTimeout(() => {
          if (textareaRef.current) {
            textareaRef.current.scrollTop = textareaRef.current.scrollHeight;
          }
        }, 50);

        toast.info(`🎙️ Live speech received: "${incomingText.slice(0, 40)}${incomingText.length > 40 ? '...' : ''}"`, {
          duration: 2500,
        });
      },
      (connected) => {
        setIsLiveConnected(connected);
      }
    );

    return () => {
      unsubscribe();
    };
  }, []);

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') return <FileType className="w-6 h-6 text-rose-500" />;
    if (ext === 'docx' || ext === 'doc') return <FileText className="w-6 h-6 text-blue-500" />;
    if (ext === 'txt') return <FileText className="w-6 h-6 text-emerald-500" />;
    return <FileAudio className="w-6 h-6 text-brand-primary" />;
  };

  const validateAndSetFile = async (file: File) => {
    setFileError(null);
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!SUPPORTED_EXTENSIONS.includes(ext) && !file.type.includes('audio') && !file.type.includes('text') && !file.type.includes('pdf')) {
      setFileError(
        `Unsupported format (${ext}). Supported formats: ${SUPPORTED_EXTENSIONS.join(', ')}`
      );
      return false;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setFileError(`File exceeds maximum allowed size of ${MAX_FILE_SIZE_LABEL}`);
      return false;
    }

    setSelectedFile(file);
    if (!title) {
      setTitle(file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' '));
    }

    // If it's a plain text file, auto-extract the text into the manual transcript area!
    if (ext === '.txt' || file.type === 'text/plain') {
      try {
        const textContent = await file.text();
        setManualTranscript(textContent);
        toast.info('Extracted text from uploaded file into transcript bar');
      } catch (err) {
        console.warn('Could not read text file directly:', err);
      }
    } else if (ext === '.pdf' || ext === '.docx' || ext === '.doc') {
      toast.success(`${file.name} ready for document text analysis`);
    }

    return true;
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleLoadSampleTranscript = () => {
    const sample = `Elena Rostova: Good afternoon everyone. Let's get straight into the agenda. We have three key objectives today: finalizing the LangGraph workflow orchestrator, setting the hard deprecation date for v1 REST endpoints, and locking in SOC-2 audit compliance readiness before November 15th.

David Chen: On the LangGraph transition, we completed benchmark runs this morning. The multi-agent state management reduced hallucination rates by 38% compared to single-prompt chains. However, memory overhead during concurrent audio chunking is peaking around 3.2 GB on our worker nodes. We need to throttle concurrent transcriptions per container to a maximum of 4.

Sarah Jenkins: Agreed on the container limit. If we set the concurrency cap to 4 per worker, our existing Kubernetes cluster can comfortably absorb the projected peak load without auto-scaling spikes. I've already prepared the Helm chart values update.

Elena Rostova: Perfect. That brings us to decision item one: we officially freeze new features on the v1 API by October 20th and redirect all customer traffic to v2 by November 15th. Does anyone have blockers with that timeline?

Marcus Vance: Sales needs at least three weeks of clear migration documentation. If engineering can supply the updated OpenAPI spec by next Monday, October 13th, my team will create the customer communication sequence and release notes by October 18th.

David Chen: I can commit to finishing the OpenAPI schema and code samples by Monday evening. Alex on my team is already wrapping up the schema validation tests.

Elena Rostova: Fantastic. To wrap up: David will finalize the OpenAPI spec by Monday, Sarah will deploy the worker concurrency limits, Marcus will draft migration docs, and I will review the final November launch deck with Arthur on Thursday.`;

    setManualTranscript(sample);
    if (!title) {
      setTitle('Executive Engineering & Product Sync');
    }
    toast.success('Loaded sample executive meeting transcript');
  };

  const handleCopyTranscript = () => {
    if (!manualTranscript) return;
    navigator.clipboard.writeText(manualTranscript);
    setHasCopied(true);
    setTimeout(() => setHasCopied(false), 2000);
    toast.success('Transcript copied to clipboard');
  };

  const handleSubmit = async (e: React.FormEvent, autoAnalyze = false) => {
    e.preventDefault();

    if (!selectedFile && !manualTranscript.trim()) {
      setFileError('Please upload a file (.pdf, .docx, .txt, audio) or enter manual transcript text.');
      return;
    }

    if (!title.trim()) {
      toast.error('Please enter a meeting title.');
      return;
    }

    setIsSubmitting(true);
    setUploadProgress(20);
    setUploadStatusText('Initializing meeting workspace...');

    try {
      const participantsList = participantsInput
        .split(',')
        .map((p) => p.trim())
        .filter(Boolean);

      let createdMeetingId = '';

      if (manualTranscript.trim() && !selectedFile) {
        // Direct manual transcript flow
        setUploadStatusText('Saving meeting transcript notes...');
        const newMeeting = await createMeeting({
          title: title.trim(),
          description: description.trim() || manualTranscript.trim().slice(0, 150),
          meetingDate: new Date(meetingDate).toISOString(),
          meetingType: meetingType as any,
          department: department.trim(),
          participants: participantsList,
          status: 'ready',
          analysisStatus: 'none',
          text: manualTranscript.trim(),
        });

        createdMeetingId = newMeeting.id;
        toast.success('Meeting transcript recorded successfully!');
      } else if (selectedFile) {
        // File upload flow (supports .pdf, .docx, .txt, .mp3, etc.)
        setUploadStatusText(`Processing ${selectedFile.name}...`);

        const result = await uploadAudioFile(
          selectedFile,
          {
            title: title.trim(),
            description: description.trim(),
            meetingDate: new Date(meetingDate).toISOString(),
            meetingType: meetingType as any,
            department: department.trim(),
            participants: participantsList,
            status: 'ready',
          },
          language,
          model,
          (progress) => {
            setUploadProgress(progress);
            if (progress < 100) {
              setUploadStatusText(`Uploading file... ${progress}%`);
            } else {
              setUploadStatusText('Extracting and processing transcript...');
            }
          },
          manualTranscript.trim() || undefined
        );

        createdMeetingId = result.meeting.id;
        toast.success('File processed and transcript created!');
      }

      // If user requested immediate analysis or clicked "Save & Analyze"
      if (autoAnalyze && createdMeetingId) {
        setUploadStatusText('Running Groq & LangGraph AI analysis...');
        const analysisResult = await triggerAnalysis(createdMeetingId);
        toast.success('AI analysis generated!');
        navigate(`/meetings/${analysisResult.id || createdMeetingId}/insights`);
      } else if (createdMeetingId) {
        navigate(`/meetings/${createdMeetingId}`);
      }
    } catch (err: any) {
      toast.error(`Operation failed: ${err.message || 'Unknown error'}`);
      setUploadStatusText('Failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const manualWordCount = manualTranscript.trim()
    ? manualTranscript.trim().split(/\s+/).length
    : 0;

  return (
    <form onSubmit={(e) => handleSubmit(e, false)} className="space-y-6 max-w-4xl mx-auto">
      {/* Live Stream Status Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-2xl bg-surface-secondary/70 dark:bg-surface-darkSecondary/40 border border-edge-light dark:border-edge-dark">
        <div className="flex items-center gap-3">
          {isLiveConnected ? (
            <div className="flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 shadow-xs">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <Mic className="w-3.5 h-3.5" />
              <span>Live Speech Stream Active</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1 rounded-full text-xs text-content-secondary bg-surface-secondary dark:bg-surface-darkSecondary border border-edge-light dark:border-edge-dark">
              <span className="inline-flex rounded-full h-2 w-2 bg-slate-400"></span>
              <span>Desktop Stream: Waiting for connection...</span>
            </div>
          )}

          {lastLiveTimestamp && (
            <span className="text-xs text-content-secondary dark:text-content-darkSecondary font-mono hidden sm:inline">
              Last spoken: {lastLiveTimestamp} ({liveSegmentCount} segments received)
            </span>
          )}
        </div>

        <div className="text-[11px] text-content-secondary flex items-center gap-1.5">
          <Radio className="w-3.5 h-3.5 text-brand-primary" />
          <span>Speech from desktop auto-streams and appends below in real-time</span>
        </div>
      </div>

      {/* Mode Switcher Banner: File Upload vs Manual Transcript */}
      <Card className="p-2 border-brand-primary/20">
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => setEntryMode('upload')}
            className={`py-3 px-4 rounded-xl text-xs sm:text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
              entryMode === 'upload'
                ? 'bg-brand-primary text-white shadow-md'
                : 'text-content-secondary hover:text-content-primary hover:bg-surface-secondary'
            }`}
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload File (.pdf, .docx, .txt, audio)</span>
          </button>

          <button
            type="button"
            onClick={() => setEntryMode('manual')}
            className={`py-3 px-4 rounded-xl text-xs sm:text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
              entryMode === 'manual'
                ? 'bg-brand-primary text-white shadow-md'
                : 'text-content-secondary hover:text-content-primary hover:bg-surface-secondary'
            }`}
          >
            <ClipboardPaste className="w-4 h-4" />
            <span>Manual / Live Speech Transcript</span>
            {liveSegmentCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-emerald-500 text-white font-mono">
                {liveSegmentCount}
              </span>
            )}
          </button>
        </div>
      </Card>

      {/* Entry Section 1: Upload File Mode */}
      {entryMode === 'upload' && (
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Meeting Recording or Document Upload</CardTitle>
              <CardDescription>
                Upload any file format: Audio (.mp3, .wav, .m4a), Documents (.pdf, .docx, .doc), or Text (.txt)
              </CardDescription>
            </div>
            <span className="text-xs text-content-secondary dark:text-content-darkSecondary">
              Max: {MAX_FILE_SIZE_LABEL}
            </span>
          </CardHeader>

          <CardContent className="space-y-4">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.doc,.txt,.mp3,.wav,.m4a,.flac,.ogg,.webm,audio/*,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
              className="hidden"
              onChange={handleFileInputChange}
            />

            {!selectedFile ? (
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all ${
                  dragActive
                    ? 'border-brand-primary bg-brand-light/30 dark:bg-brand-primary/10 scale-[1.01]'
                    : 'border-edge-light dark:border-edge-dark hover:border-brand-primary/50 hover:bg-surface-secondary/40 dark:hover:bg-surface-darkSecondary/30'
                }`}
              >
                <div className="w-16 h-16 rounded-2xl bg-brand-light dark:bg-brand-primary/15 text-brand-primary dark:text-brand-secondary flex items-center justify-center mx-auto mb-4 shadow-sm">
                  <UploadCloud className="w-8 h-8" />
                </div>

                <h4 className="text-base font-semibold text-content-primary dark:text-content-darkPrimary">
                  Drag and drop your file here
                </h4>
                <p className="text-xs text-content-secondary dark:text-content-darkSecondary mt-1">
                  Accepts audio recordings, transcripts (.txt), PDF minutes (.pdf), or Word files (.docx)
                </p>

                <div className="mt-4 flex flex-wrap items-center justify-center gap-1.5 text-[11px] text-content-secondary">
                  <span className="font-medium">Supported formats:</span>
                  {SUPPORTED_EXTENSIONS.map((ext) => (
                    <span
                      key={ext}
                      className="px-2 py-0.5 rounded bg-surface-secondary dark:bg-surface-darkSecondary text-content-secondary border border-edge-light dark:border-edge-dark uppercase font-mono text-[10px]"
                    >
                      {ext.replace('.', '')}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-xl border border-edge-light dark:border-edge-dark bg-surface-secondary/50 dark:bg-surface-darkSecondary/40 flex items-center justify-between gap-4">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-12 h-12 rounded-xl bg-brand-primary/10 flex items-center justify-center shrink-0">
                    {getFileIcon(selectedFile.name)}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-content-primary dark:text-content-darkPrimary truncate">
                      {selectedFile.name}
                    </p>
                    <p className="text-xs text-content-secondary">
                      {formatFileSize(selectedFile.size)} • {selectedFile.type || 'Document / Audio file'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={isSubmitting}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Change File
                  </Button>
                  <button
                    type="button"
                    disabled={isSubmitting}
                    onClick={() => setSelectedFile(null)}
                    className="p-1.5 rounded-lg text-content-secondary hover:text-rose-600 hover:bg-rose-50 transition-colors"
                    title="Remove file"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {fileError && (
              <div className="flex items-center gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/60 text-xs text-rose-700 dark:text-rose-300">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{fileError}</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Entry Section 2: Manual Transcript & Live Stream Input Bar */}
      <Card className={entryMode === 'manual' ? 'border-brand-primary/40 ring-1 ring-brand-primary/20' : ''}>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 w-full">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-brand-light dark:bg-brand-primary/20 text-brand-primary flex items-center justify-center">
                <ClipboardPaste className="w-4 h-4" />
              </div>
              <div>
                <CardTitle>Manual Transcript & Live Speech Input Bar</CardTitle>
                <CardDescription>
                  Live transcribed speech from desktop auto-streams here. You can also paste, edit, or append text.
                </CardDescription>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleCopyTranscript}
                disabled={!manualTranscript}
                leftIcon={hasCopied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                className="text-xs"
              >
                {hasCopied ? 'Copied' : 'Copy'}
              </Button>

              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleLoadSampleTranscript}
                className="text-xs"
              >
                Load Sample
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-2">
          <textarea
            ref={textareaRef}
            value={manualTranscript}
            onChange={(e) => {
              setManualTranscript(e.target.value);
              if (fileError) setFileError(null);
            }}
            placeholder="Live speech streams directly into this box in real-time, or paste meeting transcript text here (e.g. Elena: Let's finalize the roadmap. David: We capped container concurrency at 4...)..."
            rows={entryMode === 'manual' ? 10 : 6}
            className="w-full rounded-xl border border-edge-light dark:border-edge-dark bg-white dark:bg-surface-darkSecondary/50 p-3.5 text-xs sm:text-sm font-sans leading-relaxed text-content-primary placeholder:text-content-secondary/60 focus:outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20 resize-y"
          />

          <div className="flex items-center justify-between text-xs text-content-secondary pt-1">
            <span>
              {manualWordCount > 0 ? (
                <span className="font-medium text-brand-primary">
                  {manualWordCount.toLocaleString()} words ({manualTranscript.length.toLocaleString()} characters)
                </span>
              ) : (
                'Speak into your desktop assistant or paste notes above.'
              )}
            </span>
            {manualTranscript && (
              <button
                type="button"
                onClick={() => setManualTranscript('')}
                className="text-content-secondary hover:text-rose-600 transition-colors"
              >
                Clear text
              </button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Meeting Metadata Section */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Meeting Information</CardTitle>
            <CardDescription>Structured details for search, tracking, and reports</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Meeting Title *"
              required
              placeholder="e.g. Q4 Product Strategy Alignment"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />

            <Input
              label="Date & Time"
              type="datetime-local"
              value={meetingDate}
              onChange={(e) => setMeetingDate(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Meeting Type"
              value={meetingType}
              onChange={(e) => setMeetingType(e.target.value)}
            >
              {MEETING_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </Select>

            <Input
              label="Department / Project"
              placeholder="e.g. Product, Engineering, Sales"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
            />
          </div>

          <Input
            label="Participants (Comma-separated names or emails)"
            placeholder="Elena Rostova, David Chen, Sarah Jenkins"
            value={participantsInput}
            onChange={(e) => setParticipantsInput(e.target.value)}
            helperText="Leave blank if unknown; Whisper & LangGraph will identify distinct speaker turns."
          />

          <Textarea
            label="Optional Context & Agenda Notes"
            placeholder="Add background notes or specific questions to focus the AI analysis on..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </CardContent>
      </Card>

      {/* Transcription & Privacy Note */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Language & Inference Settings</CardTitle>
            <CardDescription>Configure language and local inference parameters</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Spoken / Document Language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {TRANSCRIPTION_LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </Select>

            <Select
              label="Whisper Model Tier"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              {WHISPER_MODELS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </Select>
          </div>

          <div className="p-3.5 rounded-xl bg-surface-secondary/70 dark:bg-surface-darkSecondary/40 border border-edge-light dark:border-edge-dark flex items-start gap-3 text-xs text-content-secondary">
            <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-content-primary dark:text-content-darkPrimary block mb-0.5">
                Privacy & Data Security Policy
              </span>
              Files and transcripts are processed locally with zero cloud training and strict zero data retention (ZDR).
            </div>
          </div>

          {/* Progress bar during submit */}
          {isSubmitting && (
            <div className="space-y-2 p-4 rounded-xl bg-brand-light/40 dark:bg-brand-primary/10 border border-brand-primary/20">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="text-brand-primary dark:text-brand-secondary">
                  {uploadStatusText}
                </span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-brand-primary h-full transition-all duration-300 ease-out"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Submission Actions */}
      <div className="flex flex-wrap items-center justify-end gap-3 pt-2">
        <Button
          type="button"
          variant="outline"
          disabled={isSubmitting}
          onClick={() => navigate('/meetings')}
        >
          Cancel
        </Button>

        <Button
          type="submit"
          variant="secondary"
          isLoading={isSubmitting}
          leftIcon={<Cpu className="w-4 h-4" />}
        >
          Start Transcription & Process
        </Button>

        <Button
          type="button"
          variant="primary"
          isLoading={isSubmitting}
          onClick={(e) => handleSubmit(e, true)}
          leftIcon={<Sparkles className="w-4 h-4" />}
          className="shadow-md shadow-brand-primary/25"
        >
          Process & Analyze with AI
        </Button>
      </div>
    </form>
  );
};
