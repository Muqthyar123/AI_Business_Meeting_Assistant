import React, { useRef, useEffect } from 'react';
import { Bell, CheckCheck, Trash2, Info, AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react';
import { useData } from '../../context/DataContext';
import { formatDateTime } from '../../utils/formatters';
import { cn } from '../../utils/cn';

interface NotificationsPopoverProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NotificationsPopover: React.FC<NotificationsPopoverProps> = ({
  isOpen,
  onClose,
}) => {
  const { notifications, markNotificationRead, clearNotifications } = useData();
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const getIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />;
      default:
        return <Info className="w-4 h-4 text-brand-primary shrink-0 mt-0.5" />;
    }
  };

  return (
    <div
      ref={popoverRef}
      className="absolute right-0 top-12 w-80 sm:w-96 rounded-2xl bg-white dark:bg-surface-darkCard border border-edge-light dark:border-edge-dark shadow-xl z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-150"
    >
      <div className="px-4 py-3 border-b border-edge-light dark:border-edge-dark flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell className="w-4 h-4 text-content-primary dark:text-content-darkPrimary" />
          <h4 className="text-sm font-semibold text-content-primary dark:text-content-darkPrimary">
            Notifications
          </h4>
        </div>
        <div className="flex items-center gap-2 text-xs">
          {notifications.length > 0 && (
            <button
              onClick={clearNotifications}
              className="text-content-secondary hover:text-content-primary flex items-center gap-1 transition-colors"
              title="Clear all"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          )}
        </div>
      </div>

      <div className="max-h-80 overflow-y-auto divide-y divide-edge-light dark:divide-edge-dark">
        {notifications.length === 0 ? (
          <div className="py-10 text-center text-xs text-content-secondary dark:text-content-darkSecondary">
            No notifications at this time.
          </div>
        ) : (
          notifications.map((n) => (
            <div
              key={n.id}
              onClick={() => markNotificationRead(n.id)}
              className={cn(
                'p-3.5 flex items-start gap-3 hover:bg-surface-secondary dark:hover:bg-surface-darkSecondary/60 transition-colors cursor-pointer text-left',
                !n.read && 'bg-brand-light/30 dark:bg-brand-primary/10'
              )}
            >
              {getIcon(n.type)}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-1">
                  <p className="text-xs font-semibold text-content-primary dark:text-content-darkPrimary truncate">
                    {n.title}
                  </p>
                  {!n.read && (
                    <span className="w-2 h-2 rounded-full bg-brand-primary shrink-0" />
                  )}
                </div>
                <p className="text-[11px] text-content-secondary dark:text-content-darkSecondary mt-0.5 leading-snug">
                  {n.message}
                </p>
                <p className="text-[10px] text-content-secondary/70 dark:text-content-darkSecondary/60 mt-1">
                  {formatDateTime(n.timestamp)}
                </p>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="px-4 py-2 border-t border-edge-light dark:border-edge-dark bg-surface-secondary/40 dark:bg-surface-darkSecondary/30 text-[10px] text-content-secondary dark:text-content-darkSecondary text-center">
        MeetMind Activity Center
      </div>
    </div>
  );
};
