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
    cyan: { stroke: '#00f5ff', glow: 'drop-shadow(0 0 6px #00f5ff)' },
    green: { stroke: '#00ff88', glow: 'drop-shadow(0 0 6px #00ff88)' },
    red: { stroke: '#ff0055', glow: 'drop-shadow(0 0 6px #ff0055)' },
    purple: { stroke: '#bf00ff', glow: 'drop-shadow(0 0 6px #bf00ff)' },
    orange: { stroke: '#ff8800', glow: 'drop-shadow(0 0 6px #ff8800)' },
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
          <span className="text-2xl font-cyber font-bold" style={{ color: c.stroke }}>
            {Math.round(progress)}%
          </span>
        )}
        {label && (
          <span className="text-xs font-mono text-gray-400 mt-1">{label}</span>
        )}
      </div>
    </div>
  );
};
