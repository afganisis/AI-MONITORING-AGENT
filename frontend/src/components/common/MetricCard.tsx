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
      iconBg: 'bg-neon-cyan/8',
      iconBorder: 'border-neon-cyan/20',
      iconColor: 'text-neon-cyan',
      valueBg: 'from-neon-cyan/10',
    },
    green: {
      iconBg: 'bg-ai-active/8',
      iconBorder: 'border-ai-active/20',
      iconColor: 'text-ai-active',
      valueBg: 'from-ai-active/10',
    },
    red: {
      iconBg: 'bg-ai-error/8',
      iconBorder: 'border-ai-error/20',
      iconColor: 'text-ai-error',
      valueBg: 'from-ai-error/10',
    },
    orange: {
      iconBg: 'bg-ai-warning/8',
      iconBorder: 'border-ai-warning/20',
      iconColor: 'text-ai-warning',
      valueBg: 'from-ai-warning/10',
    },
    yellow: {
      iconBg: 'bg-yellow-500/8',
      iconBorder: 'border-yellow-500/20',
      iconColor: 'text-yellow-400',
      valueBg: 'from-yellow-500/10',
    },
    purple: {
      iconBg: 'bg-neon-purple/8',
      iconBorder: 'border-neon-purple/20',
      iconColor: 'text-neon-purple',
      valueBg: 'from-neon-purple/10',
    },
  };

  const c = colorConfig[color];

  return (
    <Card variant="glass" hover glow={color}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs text-gray-400 tracking-wide mb-2">
            {title}
          </p>
          <div className="flex items-baseline gap-2">
            <p className={`text-4xl font-semibold ${c.iconColor}`}>
              {value}
            </p>
            {subtitle && (
              <span className="text-sm text-gray-500">{subtitle}</span>
            )}
          </div>

          {trend && (
            <div className="flex items-center mt-3 gap-2">
              {trend.isPositive ? (
                <TrendingUp className="w-4 h-4 text-ai-active" />
              ) : (
                <TrendingDown className="w-4 h-4 text-ai-error" />
              )}
              <span className={`text-sm ${trend.isPositive ? 'text-ai-active' : 'text-ai-error'}`}>
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
            transition-all duration-200
          `}
        >
          <Icon className={`w-7 h-7 ${c.iconColor}`} />
        </div>
      </div>
    </Card>
  );
};
