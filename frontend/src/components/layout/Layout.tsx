import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  AlertCircle,
  CheckCircle,
  Bot,
  Settings,
  FileText,
  Activity,
  Zap,
  Bell,
  Building2,
  TrendingUp,
} from 'lucide-react';
import clsx from 'clsx';

interface LayoutProps {
  children: React.ReactNode;
}

interface NavItem {
  label: string;
  path: string;
  icon: React.ElementType;
}

const navItems: NavItem[] = [
  { label: 'Control', path: '/', icon: Bot },
  { label: 'Activity', path: '/activity', icon: Activity },
  { label: 'Results', path: '/results', icon: TrendingUp },
];

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-cyber-900 cyber-grid-bg">
      {/* Animated background gradient */}
      <div className="fixed inset-0 bg-gradient-radial from-neon-cyan/5 via-transparent to-transparent pointer-events-none" />

      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 w-72 bg-cyber-800/80 backdrop-blur-xl border-r border-neon-cyan/20 z-20">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="h-20 flex items-center px-6 border-b border-neon-cyan/20">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-neon-cyan to-neon-purple flex items-center justify-center">
                  <Bot className="w-7 h-7 text-cyber-900" />
                </div>
                {/* Pulse ring */}
                <div
                  className="absolute inset-0 rounded-xl animate-ping bg-neon-cyan/30"
                  style={{ animationDuration: '3s' }}
                />
              </div>
              <div>
                <h1 className="text-xl font-cyber font-bold text-neon-cyan tracking-wider">
                  ZERO<span className="text-white">ELD</span>
                </h1>
                <p className="text-xs text-gray-500 font-mono tracking-widest">AI CONTROL PANEL</p>
              </div>
            </div>
          </div>

          {/* System Status */}
          <div className="px-4 py-4 border-b border-cyber-600/50">
            <div className="flex items-center justify-between p-3 rounded-lg bg-cyber-700/50 border border-neon-cyan/20">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-ai-active" />
                <span className="text-xs font-mono text-gray-400">SYSTEM</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-ai-active animate-pulse" />
                <span className="text-xs font-mono text-ai-active">ONLINE</span>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto scrollbar-hide">
            <p className="text-xs font-mono text-gray-500 uppercase tracking-widest mb-4 px-3">
              Navigation
            </p>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={clsx(
                    'group flex items-center gap-3 px-4 py-3 rounded-lg font-mono text-sm transition-all duration-300 relative overflow-hidden',
                    isActive
                      ? 'bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/30 shadow-glow-sm'
                      : 'text-gray-400 hover:bg-cyber-700/50 hover:text-gray-200 border border-transparent'
                  )}
                >
                  {/* Active indicator line */}
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-neon-cyan rounded-r shadow-neon-cyan" />
                  )}

                  <Icon
                    className={clsx(
                      'w-5 h-5 transition-all duration-300',
                      isActive ? 'text-neon-cyan' : 'group-hover:text-neon-cyan'
                    )}
                  />
                  <span className="tracking-wide">{item.label}</span>

                  {/* Hover effect */}
                  <div className="absolute inset-0 bg-gradient-to-r from-neon-cyan/0 via-neon-cyan/5 to-neon-cyan/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                </Link>
              );
            })}
          </nav>

          {/* AI Stats Mini */}
          <div className="px-4 py-4 border-t border-cyber-600/50">
            <div className="grid grid-cols-2 gap-2">
              <div className="p-3 rounded-lg bg-cyber-700/30 border border-cyber-600/50">
                <div className="flex items-center gap-2 mb-1">
                  <Zap className="w-3 h-3 text-ai-active" />
                  <span className="text-[10px] font-mono text-gray-500">FIXES</span>
                </div>
                <span className="text-lg font-bold text-ai-active font-mono">847</span>
              </div>
              <div className="p-3 rounded-lg bg-cyber-700/30 border border-cyber-600/50">
                <div className="flex items-center gap-2 mb-1">
                  <AlertCircle className="w-3 h-3 text-ai-error" />
                  <span className="text-[10px] font-mono text-gray-500">ERRORS</span>
                </div>
                <span className="text-lg font-bold text-ai-error font-mono">12</span>
              </div>
            </div>
          </div>

          {/* User */}
          <div className="p-4 border-t border-cyber-600/50">
            <div className="flex items-center gap-3 p-3 rounded-lg bg-cyber-700/30 border border-cyber-600/50 hover:border-neon-cyan/30 transition-colors cursor-pointer">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-neon-purple to-neon-cyan flex items-center justify-center">
                <span className="text-sm font-bold text-cyber-900">A</span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-200">Admin</p>
                <p className="text-xs text-gray-500 font-mono">admin@zeroeld.com</p>
              </div>
              <div className="w-2 h-2 rounded-full bg-ai-active" />
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="pl-72">
        {/* Header */}
        <header className="sticky top-0 h-16 bg-cyber-800/80 backdrop-blur-xl border-b border-cyber-600/50 flex items-center justify-between px-8 z-10">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-cyber font-semibold text-gray-100 tracking-wide">
              {navItems.find((item) => item.path === location.pathname)?.label || 'Dashboard'}
            </h2>
            <div className="h-6 w-px bg-cyber-600" />
            <span className="text-xs font-mono text-gray-500">
              {new Date().toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>

          <div className="flex items-center gap-4">
            {/* AI Status */}
            <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-ai-active/10 border border-ai-active/30">
              <div className="relative">
                <div className="w-2.5 h-2.5 rounded-full bg-ai-active" />
                <div className="absolute inset-0 rounded-full bg-ai-active animate-ping" />
              </div>
              <span className="text-sm font-mono text-ai-active tracking-wider">AI ACTIVE</span>
            </div>

            {/* Notification */}
            <button className="relative p-2 rounded-lg bg-cyber-700/50 border border-cyber-600/50 hover:border-neon-cyan/30 transition-colors">
              <Bell className="w-5 h-5 text-gray-400" />
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-ai-error text-[10px] font-bold flex items-center justify-center text-white">
                3
              </span>
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-8">{children}</main>
      </div>
    </div>
  );
};
