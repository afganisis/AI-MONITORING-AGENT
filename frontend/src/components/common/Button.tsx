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
    transition-all duration-300 ease-out
    focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-cyber-900
    disabled:opacity-50 disabled:cursor-not-allowed
    overflow-hidden
    font-mono uppercase tracking-wider
  `;

  const variants = {
    primary: `
      bg-gradient-to-r from-neon-cyan to-neon-blue text-cyber-900 font-bold
      hover:from-neon-cyan hover:to-neon-cyan
      focus:ring-neon-cyan
      ${glow ? 'shadow-[0_0_15px_rgba(0,245,255,0.3)] hover:shadow-neon-cyan' : ''}
    `,
    secondary: `
      bg-cyber-600 text-gray-100 border border-cyber-500
      hover:bg-cyber-500 hover:border-neon-cyan/50
      focus:ring-cyber-500
    `,
    success: `
      bg-gradient-to-r from-ai-active to-neon-green text-cyber-900 font-bold
      hover:shadow-neon-green
      focus:ring-neon-green
    `,
    danger: `
      bg-gradient-to-r from-ai-error to-neon-red text-white font-bold
      hover:shadow-neon-red
      focus:ring-neon-red
    `,
    warning: `
      bg-gradient-to-r from-ai-warning to-neon-orange text-cyber-900 font-bold
      hover:shadow-neon-orange
      focus:ring-neon-orange
    `,
    ghost: `
      bg-transparent text-gray-300
      hover:bg-cyber-600/50 hover:text-neon-cyan
      focus:ring-cyber-500
    `,
    cyber: `
      bg-transparent border-2 border-neon-cyan text-neon-cyan
      hover:bg-neon-cyan/10 hover:shadow-neon-cyan
      focus:ring-neon-cyan
    `,
    outline: `
      bg-transparent border border-neon-purple/50 text-neon-purple
      hover:bg-neon-purple/10 hover:border-neon-purple hover:shadow-[0_0_15px_rgba(191,0,255,0.5)]
      focus:ring-neon-purple
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
      {/* Animated shine effect */}
      <span className="absolute inset-0 overflow-hidden">
        <span className="absolute -inset-full top-0 block w-1/2 h-full bg-gradient-to-r from-transparent via-white/20 to-transparent transform -skew-x-12 animate-shine" />
      </span>

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
