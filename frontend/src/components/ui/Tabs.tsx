import React from 'react';
import { cn } from '../../utils/cn';

interface TabItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  badge?: string | number;
}

interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (tabId: string) => void;
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({ tabs, activeTab, onChange, className }) => {
  return (
    <div
      className={cn(
        'flex items-center gap-1 border-b border-edge-light dark:border-edge-dark overflow-x-auto no-scrollbar',
        className
      )}
    >
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={cn(
              'inline-flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-colors select-none',
              isActive
                ? 'border-brand-primary text-brand-primary dark:text-brand-secondary font-semibold'
                : 'border-transparent text-content-secondary dark:text-content-darkSecondary hover:text-content-primary dark:hover:text-content-darkPrimary hover:border-slate-300 dark:hover:border-slate-700'
            )}
          >
            {tab.icon && <span className="shrink-0">{tab.icon}</span>}
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span
                className={cn(
                  'text-[10px] px-1.5 py-0.5 rounded-full font-semibold',
                  isActive
                    ? 'bg-brand-primary/10 text-brand-primary dark:bg-brand-secondary/20 dark:text-brand-secondary'
                    : 'bg-slate-100 dark:bg-slate-800 text-content-secondary dark:text-content-darkSecondary'
                )}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
