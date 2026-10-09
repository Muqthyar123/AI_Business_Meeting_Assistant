import React from 'react';
import { cn } from '../../utils/cn';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helperText, leftIcon, rightIcon, ...props }, ref) => {
    return (
      <div className="w-full space-y-1.5 text-left">
        {label && (
          <label className="block text-xs font-medium text-content-primary dark:text-content-darkPrimary">
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {leftIcon && (
            <div className="absolute left-3 text-content-secondary dark:text-content-darkSecondary pointer-events-none">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            className={cn(
              'w-full rounded-[10px] border border-edge-light dark:border-edge-dark bg-white dark:bg-surface-darkSecondary/50 px-3.5 py-2 text-sm text-content-primary dark:text-content-darkPrimary placeholder:text-content-secondary/60 transition-colors focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/20 disabled:cursor-not-allowed disabled:opacity-50',
              leftIcon && 'pl-9',
              rightIcon && 'pr-9',
              error && 'border-semantic-error focus:ring-semantic-error/20',
              className
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3 text-content-secondary dark:text-content-darkSecondary">
              {rightIcon}
            </div>
          )}
        </div>
        {error ? (
          <p className="text-[11px] text-semantic-error">{error}</p>
        ) : helperText ? (
          <p className="text-[11px] text-content-secondary dark:text-content-darkSecondary">
            {helperText}
          </p>
        ) : null}
      </div>
    );
  }
);

Input.displayName = 'Input';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, helperText, ...props }, ref) => {
    return (
      <div className="w-full space-y-1.5 text-left">
        {label && (
          <label className="block text-xs font-medium text-content-primary dark:text-content-darkPrimary">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          className={cn(
            'w-full rounded-[10px] border border-edge-light dark:border-edge-dark bg-white dark:bg-surface-darkSecondary/50 px-3.5 py-2 text-sm text-content-primary dark:text-content-darkPrimary placeholder:text-content-secondary/60 transition-colors focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/20 disabled:cursor-not-allowed disabled:opacity-50 min-h-[90px]',
            error && 'border-semantic-error focus:ring-semantic-error/20',
            className
          )}
          {...props}
        />
        {error ? (
          <p className="text-[11px] text-semantic-error">{error}</p>
        ) : helperText ? (
          <p className="text-[11px] text-content-secondary dark:text-content-darkSecondary">
            {helperText}
          </p>
        ) : null}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, helperText, children, ...props }, ref) => {
    return (
      <div className="w-full space-y-1.5 text-left">
        {label && (
          <label className="block text-xs font-medium text-content-primary dark:text-content-darkPrimary">
            {label}
          </label>
        )}
        <select
          ref={ref}
          className={cn(
            'w-full rounded-[10px] border border-edge-light dark:border-edge-dark bg-white dark:bg-surface-darkSecondary px-3.5 py-2 text-sm text-content-primary dark:text-content-darkPrimary transition-colors focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/20 disabled:cursor-not-allowed disabled:opacity-50',
            error && 'border-semantic-error',
            className
          )}
          {...props}
        >
          {children}
        </select>
        {error ? (
          <p className="text-[11px] text-semantic-error">{error}</p>
        ) : helperText ? (
          <p className="text-[11px] text-content-secondary dark:text-content-darkSecondary">
            {helperText}
          </p>
        ) : null}
      </div>
    );
  }
);

Select.displayName = 'Select';
