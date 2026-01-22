import React from 'react';
import { Bot, Brain, Cpu, Zap } from 'lucide-react';

interface AIStatusIndicatorProps {
  status: 'running' | 'paused' | 'stopped' | 'processing';
  size?: 'sm' | 'md' | 'lg';
}

export const AIStatusIndicator: React.FC<AIStatusIndicatorProps> = ({
  status,
  size = 'md',
}) => {
  const sizes = {
    sm: { outer: 'w-16 h-16', inner: 'w-10 h-10', icon: 'w-5 h-5' },
    md: { outer: 'w-24 h-24', inner: 'w-16 h-16', icon: 'w-8 h-8' },
    lg: { outer: 'w-32 h-32', inner: 'w-20 h-20', icon: 'w-10 h-10' },
  };

  const statusConfig = {
    running: {
      outerColor: 'border-ai-active',
      innerColor: 'bg-ai-active',
      glowColor: 'shadow-neon-green',
      icon: Brain,
      animate: true,
    },
    paused: {
      outerColor: 'border-ai-warning',
      innerColor: 'bg-ai-warning',
      glowColor: 'shadow-neon-orange',
      icon: Cpu,
      animate: false,
    },
    stopped: {
      outerColor: 'border-gray-500',
      innerColor: 'bg-gray-500',
      glowColor: '',
      icon: Bot,
      animate: false,
    },
    processing: {
      outerColor: 'border-ai-processing',
      innerColor: 'bg-ai-processing',
      glowColor: 'shadow-neon-cyan',
      icon: Zap,
      animate: true,
    },
  };

  const config = statusConfig[status];
  const s = sizes[size];
  const Icon = config.icon;

  return (
    <div className="relative flex items-center justify-center">
      {/* Outer ring with rotation */}
      <div
        className={`
          absolute ${s.outer} rounded-full border-2 ${config.outerColor}
          ${config.animate ? 'animate-spin-slow' : ''}
        `}
      >
        {/* Segment indicators */}
        <div className={`absolute top-0 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full ${config.innerColor}`} />
        <div className={`absolute bottom-0 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full ${config.innerColor} opacity-50`} />
        <div className={`absolute left-0 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full ${config.innerColor} opacity-30`} />
        <div className={`absolute right-0 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full ${config.innerColor} opacity-30`} />
      </div>

      {/* Inner circle */}
      <div
        className={`
          ${s.inner} rounded-full ${config.innerColor} ${config.glowColor}
          flex items-center justify-center
          ${config.animate ? 'animate-pulse-slow' : ''}
        `}
      >
        <Icon className={`${s.icon} text-cyber-900`} />
      </div>

      {/* Pulse rings */}
      {config.animate && (
        <>
          <div
            className={`absolute ${s.outer} rounded-full border ${config.outerColor} animate-ping opacity-30`}
            style={{ animationDuration: '2s' }}
          />
          <div
            className={`absolute ${s.outer} rounded-full border ${config.outerColor} animate-ping opacity-20`}
            style={{ animationDuration: '3s', animationDelay: '0.5s' }}
          />
        </>
      )}
    </div>
  );
};
