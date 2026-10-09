import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/40 disabled:opacity-50 disabled:pointer-events-none select-none rounded-[10px]';

    const sizeStyles = {
      sm: 'text-xs h-8 px-3 gap-1.5',
      md: 'text-sm h-10 px-4 gap-2',
      lg: 'text-base h-11 px-5 gap-2.5',
    };

    const variantStyles = {
      primary:
        'bg-brand-primary text-white hover:bg-brand-hover shadow-sm active:scale-[0.98]',
      secondary:
        'bg-surface-secondary dark:bg-surface-darkSecondary text-content-primary dark:text-content-darkPrimary hover:bg-slate-200 dark:hover:bg-slate-700/60 active:scale-[0.98]',
      outline:
        'border border-edge-light dark:border-edge-dark bg-transparent text-content-primary dark:text-content-darkPrimary hover:bg-surface-secondary dark:hover:bg-surface-darkSecondary active:scale-[0.98]',
      ghost:
        'bg-transparent text-content-secondary dark:text-content-darkSecondary hover:text-content-primary dark:hover:text-content-darkPrimary hover:bg-surface-secondary dark:hover:bg-surface-darkSecondary',
      danger:
        'bg-semantic-error text-white hover:bg-red-700 shadow-sm active:scale-[0.98]',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(baseStyles, sizeStyles[size], variantStyles[variant], className)}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin shrink-0" />
        ) : (
          leftIcon && <span className="shrink-0">{leftIcon}</span>
        )}
        <span>{children}</span>
        {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';
