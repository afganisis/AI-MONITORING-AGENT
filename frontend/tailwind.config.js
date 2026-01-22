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
        // Основной фон - глубокий темный
        cyber: {
          900: '#0a0a0f',
          800: '#0d0d14',
          700: '#12121a',
          600: '#1a1a24',
          500: '#24242f',
        },
        // Neon Cyan - основной акцент AI
        neon: {
          cyan: '#00f5ff',
          blue: '#0080ff',
          purple: '#bf00ff',
          pink: '#ff00ff',
          green: '#00ff88',
          red: '#ff0055',
          orange: '#ff8800',
          yellow: '#ffee00',
        },
        // AI статусы
        ai: {
          active: '#00ff88',
          processing: '#00f5ff',
          warning: '#ff8800',
          error: '#ff0055',
          idle: '#6366f1',
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
        'neon-cyan': '0 0 5px #00f5ff, 0 0 20px #00f5ff, 0 0 40px #00f5ff',
        'neon-green': '0 0 5px #00ff88, 0 0 20px #00ff88, 0 0 40px #00ff88',
        'neon-red': '0 0 5px #ff0055, 0 0 20px #ff0055, 0 0 40px #ff0055',
        'neon-purple': '0 0 5px #bf00ff, 0 0 20px #bf00ff, 0 0 40px #bf00ff',
        'neon-orange': '0 0 5px #ff8800, 0 0 20px #ff8800',
        'glow-sm': '0 0 10px rgba(0, 245, 255, 0.3)',
        'glow-md': '0 0 20px rgba(0, 245, 255, 0.4)',
        'glow-lg': '0 0 30px rgba(0, 245, 255, 0.5)',
        'inner-glow': 'inset 0 0 20px rgba(0, 245, 255, 0.1)',
      },
      backgroundImage: {
        'cyber-grid': `
          linear-gradient(rgba(0, 245, 255, 0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(0, 245, 255, 0.03) 1px, transparent 1px)
        `,
        'gradient-radial': 'radial-gradient(ellipse at center, var(--tw-gradient-stops))',
        'gradient-cyber': 'linear-gradient(135deg, #0a0a0f 0%, #1a1a24 50%, #0d0d14 100%)',
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
