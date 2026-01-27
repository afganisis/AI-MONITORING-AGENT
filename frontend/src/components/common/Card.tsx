import React from 'react';
import clsx from 'clsx';

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
  glow?: 'none' | 'cyan' | 'green' | 'red' | 'purple' | 'orange';
  variant?: 'default' | 'glass' | 'bordered' | 'hologram';
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  padding = 'md',
  hover = false,
  glow = 'none',
  variant = 'default',
}) => {
  const baseStyles = 'relative rounded-xl overflow-hidden transition-all duration-200';

  const variants = {
    default: 'bg-cyber-700/50 border border-cyber-500/40',
    glass: 'bg-cyber-700/30 backdrop-blur-xl border border-neon-cyan/10 shadow-sm',
    bordered: 'bg-cyber-800/70 border border-neon-cyan/20',
    hologram: 'bg-gradient-to-br from-cyber-700/50 via-neon-cyan/3 to-cyber-700/50 border border-neon-cyan/20',
  };

  const paddings = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  const glowStyles = {
    none: '',
    cyan: 'shadow-glow-sm hover:shadow-glow-md',
    green: 'shadow-[0_0_8px_rgba(16,185,129,0.15)] hover:shadow-[0_0_16px_rgba(16,185,129,0.2)]',
    red: 'shadow-[0_0_8px_rgba(239,68,68,0.15)] hover:shadow-[0_0_16px_rgba(239,68,68,0.2)]',
    purple: 'shadow-[0_0_8px_rgba(139,92,246,0.15)] hover:shadow-[0_0_16px_rgba(139,92,246,0.2)]',
    orange: 'shadow-[0_0_8px_rgba(249,115,22,0.15)] hover:shadow-[0_0_16px_rgba(249,115,22,0.2)]',
  };

  const hoverStyles = hover ? 'hover:border-neon-cyan/30 hover:shadow-glow-md cursor-pointer hover:scale-[1.01]' : '';

  return (
    <div className={clsx(baseStyles, variants[variant], paddings[padding], glowStyles[glow], hoverStyles, className)}>
      {/* Subtle gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-white/[0.02] to-transparent pointer-events-none" />

      <div className="relative z-10">{children}</div>
    </div>
  );
};

export interface CardHeaderProps {
  title: string;
  subtitle?: string | React.ReactNode;
  action?: React.ReactNode;
  className?: string;
  icon?: React.ReactNode;
}

export const CardHeader: React.FC<CardHeaderProps> = ({
  title,
  subtitle,
  action,
  className,
  icon,
}) => {
  return (
    <div className={clsx('flex items-center justify-between mb-6', className)}>
      <div className="flex items-center gap-3">
        {icon && (
          <div className="w-10 h-10 rounded-lg bg-neon-cyan/8 border border-neon-cyan/15 flex items-center justify-center text-neon-cyan">
            {icon}
          </div>
        )}
        <div>
          <h3 className="text-lg font-semibold text-gray-100 tracking-tight">
            {title}
          </h3>
          {subtitle && (
            <p className="text-sm text-gray-400 mt-1">{subtitle}</p>
          )}
        </div>
      </div>
      {action && <div>{action}</div>}
    </div>
  );
};
