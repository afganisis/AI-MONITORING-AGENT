import React from 'react';

interface ProgressRingProps {
  progress: number; // 0-100
  size?: number;
  strokeWidth?: number;
  color?: 'cyan' | 'green' | 'red' | 'purple' | 'orange';
  showPercentage?: boolean;
  label?: string;
}

export const ProgressRing: React.FC<ProgressRingProps> = ({
  progress,
  size = 120,
  strokeWidth = 8,
  color = 'cyan',
  showPercentage = true,
  label,
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (progress / 100) * circumference;

  const colors = {
    cyan: { stroke: '#0ea5e9', glow: 'drop-shadow(0 0 4px rgba(14, 165, 233, 0.3))' },
    green: { stroke: '#10b981', glow: 'drop-shadow(0 0 4px rgba(16, 185, 129, 0.3))' },
    red: { stroke: '#ef4444', glow: 'drop-shadow(0 0 4px rgba(239, 68, 68, 0.3))' },
    purple: { stroke: '#8b5cf6', glow: 'drop-shadow(0 0 4px rgba(139, 92, 246, 0.3))' },
    orange: { stroke: '#f97316', glow: 'drop-shadow(0 0 4px rgba(249, 115, 22, 0.3))' },
  };

  const c = colors[color];

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="transparent"
          className="text-cyber-700"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={c.stroke}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
          style={{ filter: c.glow }}
        />
      </svg>

      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        {showPercentage && (
          <span className="text-2xl font-semibold" style={{ color: c.stroke }}>
            {Math.round(progress)}%
          </span>
        )}
        {label && (
          <span className="text-xs text-gray-400 mt-1">{label}</span>
        )}
      </div>
    </div>
  );
};
