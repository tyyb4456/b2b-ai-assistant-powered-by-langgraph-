import { clsx } from 'clsx';
import { AlertCircle } from 'lucide-react';

export default function Input({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  fullWidth = true,
  className = '',
  id,
  ...props
}) {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className={clsx('space-y-1.5', fullWidth && 'w-full')}>
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-neutral-700"
        >
          {label}
        </label>
      )}
      
      <div className="relative">
        {leftIcon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400">
            {leftIcon}
          </div>
        )}
        
        <input
          id={inputId}
          className={clsx(
            'input-base',
            leftIcon && 'pl-10',
            rightIcon && 'pr-10',
            error && 'input-error',
            className
          )}
          {...props}
        />
        
        {rightIcon && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400">
            {rightIcon}
          </div>
        )}
      </div>
      
      {error && (
        <div className="flex items-center gap-1.5 text-sm text-error-600">
          <AlertCircle size={14} />
          <span>{error}</span>
        </div>
      )}
      
      {helperText && !error && (
        <p className="text-sm text-neutral-500">{helperText}</p>
      )}
    </div>
  );
}

// Textarea variant
export function Textarea({
  label,
  error,
  helperText,
  fullWidth = true,
  className = '',
  rows = 4,
  id,
  ...props
}) {
  const textareaId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className={clsx('space-y-1.5', fullWidth && 'w-full')}>
      {label && (
        <label
          htmlFor={textareaId}
          className="block text-sm font-medium text-neutral-700"
        >
          {label}
        </label>
      )}
      
      <textarea
        id={textareaId}
        rows={rows}
        className={clsx(
          'input-base resize-none',
          error && 'input-error',
          className
        )}
        {...props}
      />
      
      {error && (
        <div className="flex items-center gap-1.5 text-sm text-error-600">
          <AlertCircle size={14} />
          <span>{error}</span>
        </div>
      )}
      
      {helperText && !error && (
        <p className="text-sm text-neutral-500">{helperText}</p>
      )}
    </div>
  );
}