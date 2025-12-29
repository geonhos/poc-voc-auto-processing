/**
 * Badge Component - Presentational
 */

import './Badge.css';

interface BadgeProps {
  variant: 'status' | 'urgency';
  value: string;
  className?: string;
}

export const Badge = ({ variant, value, className = '' }: BadgeProps) => {
  return (
    <span className={`badge badge-${variant} badge-${value} ${className}`}>
      {value}
    </span>
  );
};
