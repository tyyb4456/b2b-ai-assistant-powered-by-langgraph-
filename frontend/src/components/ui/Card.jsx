import { clsx } from 'clsx';

export default function Card({
  children,
  className = '',
  padding = 'default',
  hoverable = false,
  ...props
}) {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    default: 'p-6',
    lg: 'p-8',
  };

  return (
    <div
      className={clsx(
        'card',
        paddingClasses[padding],
        hoverable && 'card-hover cursor-pointer',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// Card Header
export function CardHeader({ children, className = '' }) {
  return (
    <div className={clsx('mb-4', className)}>
      {children}
    </div>
  );
}

// Card Title
export function CardTitle({ children, className = '' }) {
  return (
    <h3 className={clsx('text-lg font-semibold text-neutral-900', className)}>
      {children}
    </h3>
  );
}

// Card Description
export function CardDescription({ children, className = '' }) {
  return (
    <p className={clsx('text-sm text-neutral-600 mt-1', className)}>
      {children}
    </p>
  );
}

// Card Content
export function CardContent({ children, className = '' }) {
  return (
    <div className={clsx('space-y-4', className)}>
      {children}
    </div>
  );
}

// Card Footer
export function CardFooter({ children, className = '' }) {
  return (
    <div className={clsx('mt-6 flex items-center gap-3', className)}>
      {children}
    </div>
  );
}