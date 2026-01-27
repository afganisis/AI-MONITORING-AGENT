/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Professional dark backgrounds - more muted
        cyber: {
          900: '#0a0e1a',
          800: '#0f1419',
          700: '#141b24',
          600: '#1a2332',
          500: '#232f42',
        },
        // Refined accent colors - less neon, more professional
        neon: {
          cyan: '#0ea5e9',      // Softer cyan (sky-500)
          blue: '#3b82f6',      // Professional blue (blue-500)
          purple: '#8b5cf6',    // Muted purple (violet-500)
          pink: '#ec4899',      // Subtle pink (pink-500)
          green: '#10b981',     // Balanced green (emerald-500)
          red: '#ef4444',       // Clean red (red-500)
          orange: '#f97316',    // Professional orange (orange-500)
          yellow: '#eab308',    // Refined yellow (yellow-500)
        },
        // AI status colors - more subtle
        ai: {
          active: '#10b981',    // emerald-500
          processing: '#0ea5e9', // sky-500
          warning: '#f59e0b',   // amber-500
          error: '#ef4444',     // red-500
          idle: '#6366f1',      // indigo-500
        },
        // Legacy colors для совместимости
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        danger: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
      },
      boxShadow: {
        'neon-cyan': '0 0 10px rgba(14, 165, 233, 0.3), 0 0 20px rgba(14, 165, 233, 0.2)',
        'neon-green': '0 0 10px rgba(16, 185, 129, 0.3), 0 0 20px rgba(16, 185, 129, 0.2)',
        'neon-red': '0 0 10px rgba(239, 68, 68, 0.3), 0 0 20px rgba(239, 68, 68, 0.2)',
        'neon-purple': '0 0 10px rgba(139, 92, 246, 0.3), 0 0 20px rgba(139, 92, 246, 0.2)',
        'neon-orange': '0 0 10px rgba(249, 115, 22, 0.3), 0 0 20px rgba(249, 115, 22, 0.2)',
        'glow-sm': '0 0 8px rgba(14, 165, 233, 0.15)',
        'glow-md': '0 0 16px rgba(14, 165, 233, 0.2)',
        'glow-lg': '0 0 24px rgba(14, 165, 233, 0.25)',
        'inner-glow': 'inset 0 0 16px rgba(14, 165, 233, 0.08)',
      },
      backgroundImage: {
        'cyber-grid': `
          linear-gradient(rgba(14, 165, 233, 0.02) 1px, transparent 1px),
          linear-gradient(90deg, rgba(14, 165, 233, 0.02) 1px, transparent 1px)
        `,
        'gradient-radial': 'radial-gradient(ellipse at center, var(--tw-gradient-stops))',
        'gradient-cyber': 'linear-gradient(135deg, #0a0e1a 0%, #1a2332 50%, #0f1419 100%)',
      },
      backgroundSize: {
        'grid-sm': '20px 20px',
        'grid-md': '40px 40px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-neon': 'pulseNeon 2s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'scan': 'scan 3s linear infinite',
        'flicker': 'flicker 0.15s infinite',
        'data-stream': 'dataStream 20s linear infinite',
        'border-flow': 'borderFlow 3s linear infinite',
        'float': 'float 6s ease-in-out infinite',
        'spin-slow': 'spin 8s linear infinite',
        'shine': 'shine 3s infinite',
      },
      keyframes: {
        pulseNeon: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px #00f5ff, 0 0 10px #00f5ff' },
          '100%': { boxShadow: '0 0 10px #00f5ff, 0 0 20px #00f5ff, 0 0 30px #00f5ff' },
        },
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        flicker: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
        dataStream: {
          '0%': { backgroundPosition: '0% 0%' },
          '100%': { backgroundPosition: '0% 100%' },
        },
        borderFlow: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shine: {
          '0%': { transform: 'translateX(-100%) skewX(-12deg)' },
          '100%': { transform: 'translateX(200%) skewX(-12deg)' },
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        cyber: ['Orbitron', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
