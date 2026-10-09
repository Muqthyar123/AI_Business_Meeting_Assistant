import React from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Calendar,
  UploadCloud,
  Sparkles,
  CheckCircle2,
  ListTodo,
  Milestone,
  FileBarChart,
  History,
  Settings,
  Plus,
  ChevronLeft,
  ChevronRight,
  Database,
  Moon,
  Sun,
} from 'lucide-react';
import { Logo } from '../ui/Logo';
import { Button } from '../ui/Button';
import { useData } from '../../context/DataContext';
import { useTheme } from '../../context/ThemeContext';
import { cn } from '../../utils/cn';

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  onToggleCollapse,
  mobileOpen,
  onCloseMobile,
}) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { mode, backendHealth } = useData();
  const { effectiveTheme, toggleTheme } = useTheme();

  const mainNavItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Meetings', path: '/meetings', icon: Calendar },
    { name: 'Upload & Transcribe', path: '/meetings/new', icon: UploadCloud },
    { name: 'AI Meeting Insights', path: '/insights', icon: Sparkles },
    { name: 'Decisions', path: '/decisions', icon: CheckCircle2 },
    { name: 'Action Items', path: '/action-items', icon: ListTodo },
    { name: 'Follow-up Plans', path: '/follow-ups', icon: Milestone },
    { name: 'Reports & Exports', path: '/reports', icon: FileBarChart },
  ];

  const workspaceNavItems = [
    { name: 'Meeting History', path: '/history', icon: History },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  const sidebarContent = (
    <div className="flex flex-col h-full select-none">
      {/* Brand & Collapse Header */}
      <div className="flex items-center justify-between px-4 py-5 border-b border-edge-light dark:border-edge-dark">
        <NavLink to="/" onClick={onCloseMobile} className="flex items-center gap-3">
          <Logo collapsed={collapsed} />
        </NavLink>
        <button
          onClick={onToggleCollapse}
          className="hidden md:flex p-1.5 rounded-lg text-content-secondary hover:text-content-primary hover:bg-surface-secondary dark:hover:bg-surface-darkSecondary transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Primary New Meeting CTA */}
      <div className="p-3">
        {collapsed ? (
          <button
            onClick={() => {
              navigate('/meetings/new');
              onCloseMobile();
            }}
            title="New Meeting"
            className="w-10 h-10 mx-auto rounded-xl bg-brand-primary text-white flex items-center justify-center shadow-md shadow-brand-primary/25 hover:bg-brand-hover transition-colors"
          >
            <Plus className="w-5 h-5" />
          </button>
        ) : (
          <Button
            variant="primary"
            className="w-full justify-center shadow-md shadow-brand-primary/20"
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={() => {
              navigate('/meetings/new');
              onCloseMobile();
            }}
          >
            New Meeting
          </Button>
        )}
      </div>

      {/* Nav List */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-6">
        <div>
          {!collapsed && (
            <p className="px-3 pb-2 text-[11px] font-semibold tracking-wider uppercase text-content-secondary dark:text-content-darkSecondary">
              Main Menu
            </p>
          )}
          <nav className="space-y-1">
            {mainNavItems.map((item) => {
              const isActive =
                item.path === '/'
                  ? location.pathname === '/'
                  : location.pathname.startsWith(item.path);
              const Icon = item.icon;

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onCloseMobile}
                  title={collapsed ? item.name : undefined}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-[10px] text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-brand-light dark:bg-brand-primary/15 text-brand-primary dark:text-brand-secondary font-semibold'
                      : 'text-content-secondary dark:text-content-darkSecondary hover:text-content-primary dark:hover:text-content-darkPrimary hover:bg-surface-secondary dark:hover:bg-surface-darkSecondary/50',
                    collapsed && 'justify-center px-0 h-10'
                  )}
                >
                  <Icon className={cn('w-4 h-4 shrink-0', isActive ? 'text-brand-primary dark:text-brand-secondary' : 'opacity-80')} />
                  {!collapsed && <span className="truncate">{item.name}</span>}
                </NavLink>
              );
            })}
          </nav>
        </div>

        <div>
          {!collapsed && (
            <p className="px-3 pb-2 text-[11px] font-semibold tracking-wider uppercase text-content-secondary dark:text-content-darkSecondary">
              Workspace
            </p>
          )}
          <nav className="space-y-1">
            {workspaceNavItems.map((item) => {
              const isActive = location.pathname.startsWith(item.path);
              const Icon = item.icon;

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onCloseMobile}
                  title={collapsed ? item.name : undefined}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-[10px] text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-brand-light dark:bg-brand-primary/15 text-brand-primary dark:text-brand-secondary font-semibold'
                      : 'text-content-secondary dark:text-content-darkSecondary hover:text-content-primary dark:hover:text-content-darkPrimary hover:bg-surface-secondary dark:hover:bg-surface-darkSecondary/50',
                    collapsed && 'justify-center px-0 h-10'
                  )}
                >
                  <Icon className={cn('w-4 h-4 shrink-0', isActive ? 'text-brand-primary dark:text-brand-secondary' : 'opacity-80')} />
                  {!collapsed && <span className="truncate">{item.name}</span>}
                </NavLink>
              );
            })}
          </nav>
        </div>
      </div>

      {/* System Status & Profile Bottom Area */}
      <div className="p-3 border-t border-edge-light dark:border-edge-dark space-y-2">
        {/* Mode / Backend Indicator */}
        <div
          className={cn(
            'flex items-center gap-2 px-3 py-2 rounded-xl text-xs border',
            mode === 'demo'
              ? 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800/40 text-amber-800 dark:text-amber-300'
              : backendHealth.status === 'online'
              ? 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800/40 text-emerald-800 dark:text-emerald-300'
              : 'bg-rose-50 dark:bg-rose-950/30 border-rose-200 dark:border-rose-800/40 text-rose-800 dark:text-rose-300',
            collapsed && 'justify-center px-0'
          )}
          title={`Data Provider: ${mode.toUpperCase()} Mode`}
        >
          <Database className="w-3.5 h-3.5 shrink-0" />
          {!collapsed && (
            <div className="flex-1 truncate">
              <span className="font-semibold">{mode === 'demo' ? 'Demo Mode' : 'Live API'}</span>
              <span className="opacity-75 block text-[10px]">
                {mode === 'demo'
                  ? 'Sample Data'
                  : backendHealth.status === 'online'
                  ? 'Connected'
                  : 'Offline'}
              </span>
            </div>
          )}
        </div>

        {/* Quick Theme Switcher */}
        <button
          onClick={toggleTheme}
          className={cn(
            'w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium text-content-secondary dark:text-content-darkSecondary hover:text-content-primary hover:bg-surface-secondary/80 dark:hover:bg-surface-darkSecondary/60 transition-colors border border-transparent hover:border-edge-light dark:hover:border-edge-dark',
            collapsed && 'justify-center px-0'
          )}
          title={`Switch to ${effectiveTheme === 'dark' ? 'Light' : 'Dark'} mode`}
        >
          {effectiveTheme === 'dark' ? (
            <Sun className="w-4 h-4 text-amber-400 shrink-0" />
          ) : (
            <Moon className="w-4 h-4 shrink-0" />
          )}
          {!collapsed && (
            <span>{effectiveTheme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}</span>
          )}
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside
        className={cn(
          'hidden md:block fixed left-0 top-0 bottom-0 z-30 bg-white dark:bg-surface-darkCard border-r border-edge-light dark:border-edge-dark transition-all duration-300 ease-in-out',
          collapsed ? 'w-20' : 'w-64'
        )}
      >
        {sidebarContent}
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm"
            onClick={onCloseMobile}
          />
          <aside className="relative w-72 max-w-[85vw] h-full bg-white dark:bg-surface-darkCard shadow-2xl z-10">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
};
