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
  const baseStyles = 'relative rounded-xl overflow-hidden transition-all duration-300';

  const variants = {
    default: 'bg-cyber-700/60 border border-cyber-500/50',
    glass: 'bg-cyber-700/40 backdrop-blur-xl border border-neon-cyan/20 shadow-inner-glow',
    bordered: 'bg-cyber-800/80 border-2 border-neon-cyan/30',
    hologram: 'bg-gradient-to-br from-cyber-700/60 via-neon-cyan/5 to-cyber-700/60 border border-neon-cyan/30',
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
    green: 'shadow-[0_0_10px_rgba(0,255,136,0.3)] hover:shadow-[0_0_20px_rgba(0,255,136,0.4)]',
    red: 'shadow-[0_0_10px_rgba(255,0,85,0.3)] hover:shadow-[0_0_20px_rgba(255,0,85,0.4)]',
    purple: 'shadow-[0_0_10px_rgba(191,0,255,0.3)] hover:shadow-[0_0_20px_rgba(191,0,255,0.4)]',
    orange: 'shadow-[0_0_10px_rgba(255,136,0,0.3)] hover:shadow-[0_0_20px_rgba(255,136,0,0.4)]',
  };

  const hoverStyles = hover ? 'hover:border-neon-cyan/50 hover:shadow-glow-md cursor-pointer hover:scale-[1.02]' : '';

  return (
    <div className={clsx(baseStyles, variants[variant], paddings[padding], glowStyles[glow], hoverStyles, className)}>
      {/* Scan line эффект */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-30">
        <div className="absolute inset-0 bg-gradient-to-b from-neon-cyan/5 to-transparent h-1/2 animate-scan" />
      </div>

      {/* Corner accents */}
      <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-neon-cyan/50 rounded-tl-lg" />
      <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-neon-cyan/50 rounded-tr-lg" />
      <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-neon-cyan/50 rounded-bl-lg" />
      <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-neon-cyan/50 rounded-br-lg" />

      <div className="relative z-10">{children}</div>
    </div>
  );
};

export interface CardHeaderProps {
  title: string;
  subtitle?: string;
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
          <div className="w-10 h-10 rounded-lg bg-neon-cyan/10 border border-neon-cyan/30 flex items-center justify-center text-neon-cyan">
            {icon}
          </div>
        )}
        <div>
          <h3 className="text-lg font-semibold text-gray-100 font-cyber tracking-wide">
            {title}
          </h3>
          {subtitle && (
            <p className="text-sm text-gray-400 mt-0.5 font-mono">{subtitle}</p>
          )}
        </div>
      </div>
      {action && <div>{action}</div>}
    </div>
  );
};
