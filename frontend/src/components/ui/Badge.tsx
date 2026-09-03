import React from 'react';

export type BadgeVariant = 'critical' | 'warning' | 'neutral' | 'success';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: BadgeVariant;
}

export const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className = '', variant = 'neutral', ...props }, ref) => {
    let variantStyles = '';
    
    switch (variant) {
      case 'critical':
        variantStyles = 'bg-red-950 text-red-400 border-red-900';
        break;
      case 'warning':
        variantStyles = 'bg-yellow-950 text-yellow-400 border-yellow-900';
        break;
      case 'success':
        variantStyles = 'bg-green-950 text-green-400 border-green-900';
        break;
      case 'neutral':
      default:
        variantStyles = 'bg-zinc-800 text-zinc-300 border-zinc-700';
        break;
    }

    return (
      <div
        ref={ref}
        className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2 ${variantStyles} ${className}`}
        {...props}
      />
    );
  }
);
Badge.displayName = 'Badge';
