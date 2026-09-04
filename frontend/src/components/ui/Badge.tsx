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
        variantStyles = 'border-ember text-ember';
        break;
      case 'warning':
        variantStyles = 'border-orange-500 text-orange-600';
        break;
      case 'success':
        variantStyles = 'border-green-500 text-green-600';
        break;
      case 'neutral':
      default:
        variantStyles = 'border-ink text-ink';
        break;
    }

    return (
      <div
        ref={ref}
        className={`inline-flex items-center rounded-apple-pill border px-4 py-1.5 text-[14px] tracking-apple-body transition-colors bg-transparent ${variantStyles} ${className}`}
        {...props}
      />
    );
  }
);
Badge.displayName = 'Badge';
