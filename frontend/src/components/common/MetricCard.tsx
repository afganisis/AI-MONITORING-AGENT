import React from 'react';
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';
import { Card } from './Card';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: 'cyan' | 'green' | 'red' | 'orange' | 'yellow' | 'purple';
  subtitle?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  icon: Icon,
  trend,
  color = 'cyan',
  subtitle,
}) => {
  const colorConfig = {
    cyan: {
      iconBg: 'bg-neon-cyan/10',
      iconBorder: 'border-neon-cyan/30',
      iconColor: 'text-neon-cyan',
      valueBg: 'from-neon-cyan/20',
    },
    green: {
      iconBg: 'bg-ai-active/10',
      iconBorder: 'border-ai-active/30',
      iconColor: 'text-ai-active',
      valueBg: 'from-ai-active/20',
    },
    red: {
      iconBg: 'bg-ai-error/10',
      iconBorder: 'border-ai-error/30',
      iconColor: 'text-ai-error',
      valueBg: 'from-ai-error/20',
    },
    orange: {
      iconBg: 'bg-ai-warning/10',
      iconBorder: 'border-ai-warning/30',
      iconColor: 'text-ai-warning',
      valueBg: 'from-ai-warning/20',
    },
    yellow: {
      iconBg: 'bg-yellow-500/10',
      iconBorder: 'border-yellow-500/30',
      iconColor: 'text-yellow-400',
      valueBg: 'from-yellow-500/20',
    },
    purple: {
      iconBg: 'bg-neon-purple/10',
      iconBorder: 'border-neon-purple/30',
      iconColor: 'text-neon-purple',
      valueBg: 'from-neon-purple/20',
    },
  };

  const c = colorConfig[color];

  return (
    <Card variant="glass" hover glow={color}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-2">
            {title}
          </p>
          <div className="flex items-baseline gap-2">
            <p className={`text-4xl font-cyber font-bold ${c.iconColor}`}>
              {value}
            </p>
            {subtitle && (
              <span className="text-sm font-mono text-gray-500">{subtitle}</span>
            )}
          </div>

          {trend && (
            <div className="flex items-center mt-3 gap-2">
              {trend.isPositive ? (
                <TrendingUp className="w-4 h-4 text-ai-active" />
              ) : (
                <TrendingDown className="w-4 h-4 text-ai-error" />
              )}
              <span className={`text-sm font-mono ${trend.isPositive ? 'text-ai-active' : 'text-ai-error'}`}>
                {trend.value}%
              </span>
              <span className="text-xs text-gray-500">vs yesterday</span>
            </div>
          )}
        </div>

        <div
          className={`
            w-14 h-14 rounded-xl ${c.iconBg} border ${c.iconBorder}
            flex items-center justify-center
            relative overflow-hidden
          `}
        >
          <Icon className={`w-7 h-7 ${c.iconColor} relative z-10`} />
          {/* Animated gradient */}
          <div
            className={`
              absolute inset-0 bg-gradient-to-t ${c.valueBg} to-transparent
              animate-pulse-slow
            `}
          />
        </div>
      </div>
    </Card>
  );
};
