import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useData } from '../../context/DataContext';
import { AlertCircle, RefreshCw, Sparkles } from 'lucide-react';
import { Button } from '../ui/Button';
import { cn } from '../../utils/cn';

export const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { mode, setMode, backendHealth, checkHealth } = useData();
  const [isRetrying, setIsRetrying] = useState(false);

  const handleRetryConnection = async () => {
    setIsRetrying(true);
    await checkHealth();
    setIsRetrying(false);
  };

  return (
    <div className="min-h-screen bg-surface-bg dark:bg-surface-darkBg flex flex-col antialiased">
      {/* Sidebar */}
      <Sidebar
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed((prev) => !prev)}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      {/* Main Container */}
      <div
        className={cn(
          'flex-1 flex flex-col transition-all duration-300 ease-in-out',
          collapsed ? 'md:ml-20' : 'md:ml-64'
        )}
      >
        {/* Header */}
        <Header
          onOpenMobileSidebar={() => setMobileOpen(true)}
          collapsedSidebar={collapsed}
        />

        {/* Backend Offline Banner (shown in API mode if offline) */}
        {mode === 'api' && backendHealth.status !== 'online' && (
          <div className="bg-amber-50 dark:bg-amber-950/60 border-b border-amber-200 dark:border-amber-800/60 px-4 py-2.5 text-xs text-amber-900 dark:text-amber-200 flex flex-wrap items-center justify-between gap-3 animate-in fade-in">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
              <span>
                Unable to connect to the MeetMind FastAPI backend. Check that{' '}
                <code className="font-mono bg-amber-100 dark:bg-amber-900/60 px-1 py-0.5 rounded">
                  localhost:8000
                </code>{' '}
                is running.
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs border-amber-300 hover:bg-amber-100"
                isLoading={isRetrying}
                leftIcon={<RefreshCw className="w-3 h-3" />}
                onClick={handleRetryConnection}
              >
                Retry
              </Button>
              <Button
                variant="primary"
                size="sm"
                className="h-7 text-xs bg-amber-600 hover:bg-amber-700 text-white"
                leftIcon={<Sparkles className="w-3 h-3" />}
                onClick={() => setMode('demo')}
              >
                Switch to Demo Mode
              </Button>
            </div>
          </div>
        )}

        {/* Page Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
