import React, { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import {
  Menu,
  Search,
  Bell,
  Sun,
  Moon,
  ChevronRight,
  Database,
  RefreshCw,
  SlidersHorizontal,
} from 'lucide-react';
import { useData } from '../../context/DataContext';
import { useTheme } from '../../context/ThemeContext';
import { NotificationsPopover } from './NotificationsPopover';
import { GlobalSearchModal } from './GlobalSearchModal';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { cn } from '../../utils/cn';

interface HeaderProps {
  onOpenMobileSidebar: () => void;
  collapsedSidebar: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onOpenMobileSidebar, collapsedSidebar }) => {
  const location = useLocation();
  const { mode, setMode, backendHealth, checkHealth, unreadNotificationCount, resetDemoData } =
    useData();
  const { effectiveTheme, toggleTheme } = useTheme();

  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isModeModalOpen, setIsModeModalOpen] = useState(false);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);

  // Derive human-readable breadcrumb / title
  const getBreadcrumbs = () => {
    const path = location.pathname;
    if (path === '/') return [{ label: 'Dashboard', path: '/' }];
    if (path.startsWith('/meetings/new'))
      return [
        { label: 'Meetings', path: '/meetings' },
        { label: 'Upload & Transcribe', path: '/meetings/new' },
      ];
    if (path.startsWith('/meetings')) {
      const parts = path.split('/').filter(Boolean);
      if (parts.length === 1) return [{ label: 'Meetings', path: '/meetings' }];
      if (parts.length >= 2) {
        return [
          { label: 'Meetings', path: '/meetings' },
          { label: 'Meeting Details', path: `/meetings/${parts[1]}` },
        ];
      }
    }
    if (path.startsWith('/insights'))
      return [{ label: 'AI Meeting Insights', path: '/insights' }];
    if (path.startsWith('/decisions')) return [{ label: 'Decisions', path: '/decisions' }];
    if (path.startsWith('/action-items'))
      return [{ label: 'Action Items', path: '/action-items' }];
    if (path.startsWith('/follow-ups'))
      return [{ label: 'Follow-up Plans', path: '/follow-ups' }];
    if (path.startsWith('/reports')) return [{ label: 'Reports & Exports', path: '/reports' }];
    if (path.startsWith('/history')) return [{ label: 'Meeting History', path: '/history' }];
    if (path.startsWith('/settings')) return [{ label: 'Settings', path: '/settings' }];
    return [{ label: 'MeetMind', path: '/' }];
  };

  const breadcrumbs = getBreadcrumbs();

  const handleManualHealthCheck = async () => {
    setIsCheckingHealth(true);
    await checkHealth();
    setIsCheckingHealth(false);
  };

  return (
    <>
      <header
        className={cn(
          'sticky top-0 z-20 h-16 bg-white/80 dark:bg-surface-darkCard/80 backdrop-blur-md border-b border-edge-light dark:border-edge-dark flex items-center justify-between px-4 sm:px-6 transition-all'
        )}
      >
        {/* Left: Mobile Toggle & Breadcrumbs */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenMobileSidebar}
            className="md:hidden p-2 rounded-lg text-content-secondary hover:text-content-primary hover:bg-surface-secondary dark:hover:bg-surface-darkSecondary transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>

          <nav className="flex items-center space-x-1.5 text-xs sm:text-sm font-medium">
            {breadcrumbs.map((b, i) => (
              <React.Fragment key={b.path}>
                {i > 0 && (
                  <ChevronRight className="w-3.5 h-3.5 text-content-secondary/60 dark:text-content-darkSecondary/60 shrink-0" />
                )}
                {i === breadcrumbs.length - 1 ? (
                  <span className="text-content-primary dark:text-content-darkPrimary font-semibold truncate max-w-[150px] sm:max-w-[260px]">
                    {b.label}
                  </span>
                ) : (
                  <Link
                    to={b.path}
                    className="text-content-secondary dark:text-content-darkSecondary hover:text-content-primary dark:hover:text-content-darkPrimary transition-colors truncate"
                  >
                    {b.label}
                  </Link>
                )}
              </React.Fragment>
            ))}
          </nav>
        </div>

        {/* Right: Search, Mode Pill, Notifications, Theme, Status */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Global Search Button */}
          <button
            onClick={() => setIsSearchOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-edge-light dark:border-edge-dark bg-surface-secondary/50 dark:bg-surface-darkSecondary/50 text-content-secondary dark:text-content-darkSecondary hover:text-content-primary hover:border-slate-300 dark:hover:border-slate-600 transition-colors text-xs"
          >
            <Search className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Search...</span>
            <kbd className="hidden md:inline-block px-1.5 py-0.5 text-[10px] rounded bg-white dark:bg-surface-darkCard border border-edge-light dark:border-edge-dark font-mono">
              ⌘K
            </kbd>
          </button>

          {/* Mode Switcher Pill */}
          <button
            onClick={() => setIsModeModalOpen(true)}
            className={cn(
              'flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold border transition-all',
              mode === 'demo'
                ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-700 hover:bg-amber-100'
                : backendHealth.status === 'online'
                ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-700 hover:bg-emerald-100'
                : 'bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-300 border-rose-300 dark:border-rose-700 hover:bg-rose-100'
            )}
            title="Click to configure Data Provider & Backend connection"
          >
            <span
              className={cn(
                'w-2 h-2 rounded-full',
                mode === 'demo'
                  ? 'bg-amber-500'
                  : backendHealth.status === 'online'
                  ? 'bg-emerald-500'
                  : 'bg-rose-500'
              )}
            />
            <span className="hidden xs:inline">
              {mode === 'demo' ? 'Demo Mode' : 'Live API'}
            </span>
          </button>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setIsNotificationsOpen((prev) => !prev)}
              className="relative p-2 rounded-xl text-content-secondary hover:text-content-primary hover:bg-surface-secondary dark:hover:bg-surface-darkSecondary transition-colors"
              title="Notifications"
            >
              <Bell className="w-4 h-4" />
              {unreadNotificationCount > 0 && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-brand-primary" />
              )}
            </button>
            <NotificationsPopover
              isOpen={isNotificationsOpen}
              onClose={() => setIsNotificationsOpen(false)}
            />
          </div>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-xl text-content-secondary hover:text-content-primary hover:bg-surface-secondary dark:hover:bg-surface-darkSecondary transition-colors"
            title="Toggle theme"
          >
            {effectiveTheme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-400" />
            ) : (
              <Moon className="w-4 h-4" />
            )}
          </button>
        </div>
      </header>

      {/* Global Search Modal */}
      <GlobalSearchModal isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />

      {/* Data Provider / Backend Switch Modal */}
      <Modal
        isOpen={isModeModalOpen}
        onClose={() => setIsModeModalOpen(false)}
        title="Data Provider & Backend Connection"
        description="Configure whether MeetMind uses realistic local demo data or the live Python FastAPI backend."
        maxWidth="md"
        footer={
          <Button variant="secondary" size="sm" onClick={() => setIsModeModalOpen(false)}>
            Close
          </Button>
        }
      >
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-content-secondary dark:text-content-darkSecondary">
              Active Environment Mode
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setMode('demo')}
                className={cn(
                  'p-3.5 rounded-xl border text-left transition-all',
                  mode === 'demo'
                    ? 'border-brand-primary bg-brand-light/30 dark:bg-brand-primary/10 ring-2 ring-brand-primary/20'
                    : 'border-edge-light dark:border-edge-dark hover:bg-surface-secondary'
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Database className="w-4 h-4 text-brand-primary" />
                  <span className="text-xs font-semibold">Demo Mode</span>
                </div>
                <p className="text-[11px] text-content-secondary leading-snug">
                  Rich preloaded executive datasets, instant transcription & AI simulation.
                </p>
              </button>

              <button
                onClick={() => setMode('api')}
                className={cn(
                  'p-3.5 rounded-xl border text-left transition-all',
                  mode === 'api'
                    ? 'border-brand-primary bg-brand-light/30 dark:bg-brand-primary/10 ring-2 ring-brand-primary/20'
                    : 'border-edge-light dark:border-edge-dark hover:bg-surface-secondary'
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <SlidersHorizontal className="w-4 h-4 text-brand-primary" />
                  <span className="text-xs font-semibold">Live FastAPI</span>
                </div>
                <p className="text-[11px] text-content-secondary leading-snug">
                  Connects to FastAPI, local Whisper, Groq, LangGraph, and MongoDB.
                </p>
              </button>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-surface-secondary/50 dark:bg-surface-darkSecondary/50 border border-edge-light dark:border-edge-dark space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium">FastAPI Backend Status:</span>
              <div className="flex items-center gap-1.5">
                <span
                  className={cn(
                    'w-2 h-2 rounded-full',
                    backendHealth.status === 'online'
                      ? 'bg-emerald-500'
                      : backendHealth.status === 'degraded'
                      ? 'bg-amber-500'
                      : 'bg-rose-500'
                  )}
                />
                <span className="text-xs font-semibold capitalize">
                  {backendHealth.status}
                </span>
              </div>
            </div>

            <div className="text-[11px] text-content-secondary space-y-1">
              <p>Base URL: <code className="font-mono text-brand-primary">http://localhost:8000</code></p>
              {backendHealth.message && (
                <p className="text-rose-500">{backendHealth.message}</p>
              )}
            </div>

            <div className="pt-1 flex items-center justify-between">
              <Button
                variant="outline"
                size="sm"
                isLoading={isCheckingHealth}
                leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
                onClick={handleManualHealthCheck}
              >
                Test Connection
              </Button>

              {mode === 'demo' && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetDemoData}
                  className="text-xs text-content-secondary"
                >
                  Reset Demo Store
                </Button>
              )}
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
};
