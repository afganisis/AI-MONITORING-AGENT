import React from 'react';
import clsx from 'clsx';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'ghost' | 'cyber' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  glow?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  className,
  glow = true,
  ...props
}) => {
  const baseStyles = `
    relative inline-flex items-center justify-center font-medium rounded-lg
    transition-all duration-200 ease-out
    focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-cyber-900
    disabled:opacity-50 disabled:cursor-not-allowed
    overflow-hidden
    font-mono tracking-wide
  `;

  const variants = {
    primary: `
      bg-neon-cyan text-white font-semibold
      hover:bg-neon-cyan/90
      focus:ring-neon-cyan/50
      ${glow ? 'shadow-glow-sm hover:shadow-glow-md' : ''}
    `,
    secondary: `
      bg-cyber-600 text-gray-100 border border-cyber-500/50
      hover:bg-cyber-500 hover:border-cyber-400
      focus:ring-cyber-500/50
    `,
    success: `
      bg-ai-active text-white font-semibold
      hover:bg-ai-active/90
      focus:ring-ai-active/50
      ${glow ? 'shadow-[0_0_8px_rgba(16,185,129,0.2)] hover:shadow-[0_0_16px_rgba(16,185,129,0.3)]' : ''}
    `,
    danger: `
      bg-ai-error text-white font-semibold
      hover:bg-ai-error/90
      focus:ring-ai-error/50
      ${glow ? 'shadow-[0_0_8px_rgba(239,68,68,0.2)] hover:shadow-[0_0_16px_rgba(239,68,68,0.3)]' : ''}
    `,
    warning: `
      bg-ai-warning text-white font-semibold
      hover:bg-ai-warning/90
      focus:ring-ai-warning/50
      ${glow ? 'shadow-[0_0_8px_rgba(245,158,11,0.2)] hover:shadow-[0_0_16px_rgba(245,158,11,0.3)]' : ''}
    `,
    ghost: `
      bg-transparent text-gray-300
      hover:bg-cyber-600/40 hover:text-gray-100
      focus:ring-cyber-500/50
    `,
    cyber: `
      bg-transparent border border-neon-cyan/60 text-neon-cyan
      hover:bg-neon-cyan/10 hover:border-neon-cyan
      focus:ring-neon-cyan/50
    `,
    outline: `
      bg-transparent border border-neon-purple/60 text-neon-purple
      hover:bg-neon-purple/10 hover:border-neon-purple
      focus:ring-neon-purple/50
    `,
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-5 py-2.5 text-sm',
    lg: 'px-8 py-3.5 text-base',
  };

  return (
    <button
      className={clsx(baseStyles, variants[variant], sizes[size], className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      <span className="relative z-10">{children}</span>
    </button>
  );
};
