import { Loader2 } from 'lucide-react';
import { clsx } from 'clsx';

const sizes = {
  sm: 16,
  md: 24,
  lg: 32,
  xl: 48,
};

export default function Spinner({
  size = 'md',
  className = '',
  text = '',
}) {
  return (
    <div className={clsx('flex flex-col items-center justify-center gap-3', className)}>
      <Loader2
        size={sizes[size]}
        className="animate-spin text-primary-600"
      />
      {text && (
        <p className="text-sm text-neutral-600">{text}</p>
      )}
    </div>
  );
}

// Full page spinner overlay
export function SpinnerOverlay({ text = 'Loading...' }) {
  return (
    <div className="fixed inset-0 bg-white/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <Spinner size="lg" text={text} />
    </div>
  );
}