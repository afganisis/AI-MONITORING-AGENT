import React from 'react';
import clsx from 'clsx';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'danger' | 'warning' | 'info' | 'processing' | 'ai';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  pulse?: boolean;
  glow?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  className,
  pulse = false,
  glow = false,
}) => {
  const baseStyles = `
    inline-flex items-center font-mono uppercase tracking-wider
    rounded-md border transition-all duration-300
  `;

  const variants = {
    default: 'bg-cyber-600/50 text-gray-300 border-cyber-500',
    success: `
      bg-ai-active/10 text-ai-active border-ai-active/30
      ${glow ? 'shadow-[0_0_10px_rgba(0,255,136,0.2)]' : ''}
    `,
    danger: `
      bg-ai-error/10 text-ai-error border-ai-error/30
      ${glow ? 'shadow-[0_0_10px_rgba(255,0,85,0.2)]' : ''}
    `,
    warning: `
      bg-ai-warning/10 text-ai-warning border-ai-warning/30
      ${glow ? 'shadow-[0_0_10px_rgba(255,136,0,0.2)]' : ''}
    `,
    info: `
      bg-neon-blue/10 text-neon-blue border-neon-blue/30
      ${glow ? 'shadow-[0_0_10px_rgba(0,128,255,0.2)]' : ''}
    `,
    processing: `
      bg-ai-processing/10 text-ai-processing border-ai-processing/30
      ${glow ? 'shadow-[0_0_10px_rgba(0,245,255,0.2)]' : ''}
    `,
    ai: `
      bg-gradient-to-r from-neon-cyan/10 to-neon-purple/10
      text-neon-cyan border-neon-cyan/30
      ${glow ? 'shadow-[0_0_10px_rgba(0,245,255,0.2)]' : ''}
    `,
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-[10px]',
    md: 'px-3 py-1 text-xs',
    lg: 'px-4 py-1.5 text-sm',
  };

  const pulseStyles = pulse ? 'animate-pulse-neon' : '';

  return (
    <span className={clsx(baseStyles, variants[variant], sizes[size], pulseStyles, className)}>
      {(variant === 'processing' || pulse) && (
        <span className="w-1.5 h-1.5 rounded-full bg-current mr-2 animate-pulse" />
      )}
      {children}
    </span>
  );
};

// Status Badge специально для AI статусов
export interface StatusBadgeProps {
  status: 'online' | 'offline' | 'processing' | 'error' | 'idle';
  label?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label }) => {
  const statusConfig = {
    online: { variant: 'success' as const, text: label || 'ONLINE', pulse: true, glow: true },
    offline: { variant: 'default' as const, text: label || 'OFFLINE', pulse: false, glow: false },
    processing: { variant: 'processing' as const, text: label || 'PROCESSING', pulse: true, glow: true },
    error: { variant: 'danger' as const, text: label || 'ERROR', pulse: true, glow: true },
    idle: { variant: 'info' as const, text: label || 'IDLE', pulse: false, glow: false },
  };

  const config = statusConfig[status];

  return (
    <Badge variant={config.variant} pulse={config.pulse} glow={config.glow}>
      {config.text}
    </Badge>
  );
};
