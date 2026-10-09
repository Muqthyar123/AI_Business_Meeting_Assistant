import React, { useState } from 'react';
import {
  Settings,
  Moon,
  Sun,
  Monitor,
  Shield,
  Database,
  RefreshCw,
  CheckCircle2,
  Trash2,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { useTheme } from '../context/ThemeContext';
import { useData } from '../context/DataContext';
import { ENV } from '../config/environment';
import { toast } from 'sonner';

export const SettingsPage: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const { mode, setMode, backendHealth, checkHealth, resetDemoData } = useData();

  const [isCheckingHealth, setIsCheckingHealth] = useState(false);

  const handleTestBackend = async () => {
    setIsCheckingHealth(true);
    await checkHealth();
    setIsCheckingHealth(false);
    toast.success('Connection health check executed');
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-content-primary dark:text-content-darkPrimary flex items-center gap-2.5">
          <Settings className="w-6 h-6 text-brand-primary" />
          Settings & Configuration
        </h1>
        <p className="text-xs sm:text-sm text-content-secondary dark:text-content-darkSecondary mt-0.5">
          Manage system preferences, appearance, and FastAPI backend connectivity
        </p>
      </div>

      {/* Appearance Theme */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Sun className="w-4 h-4 text-brand-primary" />
            <CardTitle>Appearance & Theme</CardTitle>
          </div>
          <CardDescription>Select your preferred visual style</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { id: 'light', label: 'Light Mode', icon: Sun, desc: 'Crisp high-contrast theme' },
              { id: 'dark', label: 'Dark Mode', icon: Moon, desc: 'Deep navy executive theme' },
              { id: 'system', label: 'System Default', icon: Monitor, desc: 'Syncs with OS settings' },
            ].map((t) => {
              const Icon = t.icon;
              const isSelected = theme === t.id;

              return (
                <button
                  key={t.id}
                  onClick={() => setTheme(t.id as any)}
                  className={`p-4 rounded-xl border text-left transition-all ${
                    isSelected
                      ? 'border-brand-primary bg-brand-light/30 dark:bg-brand-primary/15 ring-2 ring-brand-primary/20'
                      : 'border-edge-light dark:border-edge-dark hover:bg-surface-secondary/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <Icon className={`w-5 h-5 ${isSelected ? 'text-brand-primary' : 'text-content-secondary'}`} />
                    {isSelected && <CheckCircle2 className="w-4 h-4 text-brand-primary" />}
                  </div>
                  <h4 className="text-xs font-semibold text-content-primary dark:text-content-darkPrimary">
                    {t.label}
                  </h4>
                  <p className="text-[11px] text-content-secondary mt-0.5">{t.desc}</p>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Backend Integration & Environment Mode */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-brand-primary" />
            <CardTitle>FastAPI Backend & Data Provider</CardTitle>
          </div>
          <CardDescription>
            Switch between local demo workspace and live FastAPI Python server
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div
              onClick={() => setMode('demo')}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                mode === 'demo'
                  ? 'border-brand-primary bg-brand-light/30 dark:bg-brand-primary/10 ring-2 ring-brand-primary/20'
                  : 'border-edge-light dark:border-edge-dark hover:bg-surface-secondary/40'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-amber-700 dark:text-amber-400">
                  Demo Mode (Active)
                </span>
                {mode === 'demo' && <CheckCircle2 className="w-4 h-4 text-brand-primary" />}
              </div>
              <p className="text-xs text-content-secondary">
                Uses realistic executive meeting datasets with simulated local Whisper and Groq reasoning.
              </p>
            </div>

            <div
              onClick={() => setMode('api')}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                mode === 'api'
                  ? 'border-brand-primary bg-brand-light/30 dark:bg-brand-primary/10 ring-2 ring-brand-primary/20'
                  : 'border-edge-light dark:border-edge-dark hover:bg-surface-secondary/40'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-emerald-700 dark:text-emerald-400">
                  Live FastAPI Mode
                </span>
                {mode === 'api' && <CheckCircle2 className="w-4 h-4 text-brand-primary" />}
              </div>
              <p className="text-xs text-content-secondary">
                Connects directly to your Python FastAPI backend at {ENV.API_BASE_URL}.
              </p>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-surface-secondary/50 dark:bg-surface-darkSecondary/40 border border-edge-light dark:border-edge-dark space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-content-primary">Backend Server Health:</span>
              <span
                className={`px-2 py-0.5 rounded-full font-semibold capitalize ${
                  backendHealth.status === 'online'
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-rose-50 text-rose-700 border border-rose-200'
                }`}
              >
                {backendHealth.status}
              </span>
            </div>
            <p className="text-content-secondary">
              Base Endpoint:{' '}
              <code className="font-mono text-brand-primary">{ENV.API_BASE_URL}</code>
            </p>

            <div className="pt-2 flex items-center justify-between">
              <Button
                variant="outline"
                size="sm"
                isLoading={isCheckingHealth}
                onClick={handleTestBackend}
                leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
              >
                Test Connection
              </Button>

              {mode === 'demo' && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetDemoData}
                  className="text-xs text-rose-600 hover:bg-rose-50"
                  leftIcon={<Trash2 className="w-3.5 h-3.5" />}
                >
                  Reset Demo Data
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>


      {/* Privacy and Security Policy */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-emerald-600" />
            <CardTitle>Privacy & Data Retention</CardTitle>
          </div>
          <CardDescription>Security architecture principles</CardDescription>
        </CardHeader>
        <CardContent className="text-xs text-content-secondary space-y-2 leading-relaxed">
          <p>
            MeetMind is designed for enterprise privacy. Audio recordings are transmitted only to your configured local or VPC FastAPI server where OpenAI Whisper runs on-premises.
          </p>
          <p>
            AI meeting analysis queries Groq under Zero Data Retention (ZDR) agreements. Private API keys and database credentials are never stored or exposed on the client frontend.
          </p>
        </CardContent>
      </Card>

      {/* Application Information */}
      <Card className="p-4 text-xs text-content-secondary flex flex-wrap items-center justify-between gap-2">
        <span>MeetMind Web Assistant — Version {ENV.APP_VERSION}</span>
        <span>Build: {ENV.BUILD_DATE} • FastAPI + Groq + LangGraph ready</span>
      </Card>
    </div>
  );
};
