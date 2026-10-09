import React from 'react';

interface LogoProps {
  collapsed?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const Logo: React.FC<LogoProps> = ({ collapsed = false, className = '', size = 'md' }) => {
  const iconSize = size === 'sm' ? 28 : size === 'lg' ? 40 : 34;
  const textSize = size === 'sm' ? 'text-lg' : size === 'lg' ? 'text-2xl' : 'text-xl';

  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      {/* Custom Geometric Logo: Speech bubble + connected nodes + waveform */}
      <div
        className="relative flex items-center justify-center rounded-xl bg-gradient-to-tr from-brand-primary to-brand-secondary shadow-md shadow-brand-primary/20 shrink-0"
        style={{ width: iconSize, height: iconSize }}
      >
        <svg
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-5/6 h-5/6 text-white"
        >
          {/* Subtle speech outline */}
          <path
            d="M6 10C6 7.79 7.79 6 10 6H22C24.21 6 26 7.79 26 10V18C26 20.21 24.21 22 22 22H15L9 26V22H10C7.79 22 6 20.21 6 18V10Z"
            fill="white"
            fillOpacity="0.18"
          />
          {/* Connected intelligent nodes */}
          <circle cx="11" cy="14" r="2.2" fill="#35C9D8" />
          <circle cx="16" cy="11.5" r="2.2" fill="#FFFFFF" />
          <circle cx="21" cy="14" r="2.2" fill="#E0DDFE" />
          <line x1="11" y1="14" x2="16" y2="11.5" stroke="#FFFFFF" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="16" y1="11.5" x2="21" y2="14" stroke="#FFFFFF" strokeWidth="1.5" strokeLinecap="round" />
          {/* Action checkmark/waveform touch */}
          <path
            d="M11 17.5L14.5 20L21 16"
            stroke="#35C9D8"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      {!collapsed && (
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className={`font-bold tracking-tight text-content-primary dark:text-content-darkPrimary ${textSize}`}>
              Meet<span className="text-brand-primary dark:text-brand-secondary">Mind</span>
            </span>
          </div>
          <span className="text-[10px] font-medium tracking-wide uppercase text-content-secondary dark:text-content-darkSecondary">
            AI Meeting Assistant
          </span>
        </div>
      )}
    </div>
  );
};
