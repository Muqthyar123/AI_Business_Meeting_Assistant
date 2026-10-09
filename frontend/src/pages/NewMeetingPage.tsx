import React from 'react';
import { AudioUploader } from '../components/transcription/AudioUploader';
import { UploadCloud, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';

export const NewMeetingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          leftIcon={<ArrowLeft className="w-4 h-4" />}
          onClick={() => navigate('/meetings')}
        >
          Back to Meetings
        </Button>
      </div>

      <div className="text-center max-w-xl mx-auto space-y-1.5">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-content-primary dark:text-content-darkPrimary">
          Record or Upload Meeting Audio
        </h1>
        <p className="text-xs sm:text-sm text-content-secondary dark:text-content-darkSecondary">
          Whisper transcribes speech locally on your backend server. Groq and LangGraph extract structured decisions, action items, and follow-up plans.
        </p>
      </div>

      {/* Main Upload Workflow */}
      <AudioUploader />
    </div>
  );
};
