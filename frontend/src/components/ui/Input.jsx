import { clsx } from 'clsx';
import { AlertCircle } from 'lucide-react';

const baseInputClasses = 'w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed';

const errorClasses = 'border-red-500 focus:ring-red-500 focus:border-red-500 text-red-600';

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
        <label htmlFor={inputId} className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}

      <div className="relative">
        {leftIcon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
            {leftIcon}
          </div>
        )}

        <input
          id={inputId}
          className={clsx(
            baseInputClasses,
            leftIcon && 'pl-10',
            rightIcon && 'pr-10',
            error && errorClasses,
            className
          )}
          {...props}
        />

        {rightIcon && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
            {rightIcon}
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-1.5 text-sm text-red-600 mt-1">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {helperText && !error && (
        <p className="text-sm text-gray-500 mt-1">{helperText}</p>
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
        <label htmlFor={textareaId} className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}

      <textarea
        id={textareaId}
        rows={rows}
        className={clsx(
          baseInputClasses,
          'resize-none min-h-[100px] leading-relaxed',
          error && errorClasses,
          className
        )}
        {...props}
      />

      {error && (
        <div className="flex items-center gap-1.5 text-sm text-red-600 mt-1">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {helperText && !error && (
        <p className="text-sm text-gray-500 mt-1">{helperText}</p>
      )}
    </div>
  );
}
