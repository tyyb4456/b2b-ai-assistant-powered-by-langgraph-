import { clsx } from 'clsx';

const variants = {
  success: 'badge-success',
  warning: 'badge-warning',
  error: 'badge-error',
  info: 'badge-info',
  neutral: 'badge-neutral',
};

export default function Badge({
  children,
  variant = 'neutral',
  className = '',
  ...props
}) {
  return (
    <span
      className={clsx('badge', variants[variant], className)}
      {...props}
    >
      {children}
    </span>
  );
}

// Status Badge with icon
export function StatusBadge({ status, className = '' }) {
  const statusConfig = {
    completed: { variant: 'success', label: 'Completed', icon: '✓' },
    quote_generated: { variant: 'success', label: 'Quote Generated', icon: '📄' },
    in_progress: { variant: 'warning', label: 'In Progress', icon: '⏳' },
    paused: { variant: 'warning', label: 'Paused', icon: '⏸' },
    failed: { variant: 'error', label: 'Failed', icon: '✗' },
    negotiating: { variant: 'info', label: 'Negotiating', icon: '🤝' },
    message_sent: { variant: 'info', label: 'Message Sent', icon: '📧' },
  };

  const config = statusConfig[status] || statusConfig.in_progress;

  return (
    <Badge variant={config.variant} className={className}>
      <span className="mr-1">{config.icon}</span>
      {config.label}
    </Badge>
  );
}