import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Bot,
  Activity,
  TrendingUp,
  LogOut,
} from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '../../contexts/AuthContext';

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
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const userInitial = user?.username?.charAt(0).toUpperCase() || 'U';
  const displayName = user?.full_name || user?.username || 'User';
  const displayEmail = user?.email || '';

  return (
    <div className="min-h-screen bg-cyber-900">
      {/* Subtle background gradient */}
      <div className="fixed inset-0 bg-gradient-radial from-neon-cyan/3 via-transparent to-transparent pointer-events-none" />

      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 w-72 bg-cyber-800/90 backdrop-blur-xl border-r border-cyber-600/40 z-20">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="h-20 flex items-center px-6 border-b border-cyber-600/40">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-neon-cyan/20 to-neon-purple/20 border border-neon-cyan/30 flex items-center justify-center">
                <Bot className="w-7 h-7 text-neon-cyan" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-white">
                  PTHORA<span className="text-neon-cyan">.AI</span>
                </h1>
                <p className="text-xs text-gray-500 tracking-wide">ELD Monitoring System</p>
              </div>
            </div>
          </div>

          {/* System Status */}
          <div className="px-4 py-4 border-b border-cyber-600/40">
            <div className="flex items-center justify-between p-3 rounded-lg bg-cyber-700/40 border border-cyber-600/50">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-ai-active" />
                <span className="text-xs text-gray-400">System</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-ai-active" />
                <span className="text-xs text-ai-active">Online</span>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto scrollbar-hide">
            <p className="text-xs text-gray-500 tracking-wide mb-4 px-3">
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
                    'group flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-all duration-200 relative',
                    isActive
                      ? 'bg-neon-cyan/8 text-neon-cyan border border-neon-cyan/20'
                      : 'text-gray-400 hover:bg-cyber-700/40 hover:text-gray-200 border border-transparent'
                  )}
                >
                  {/* Active indicator line */}
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-neon-cyan rounded-r" />
                  )}

                  <Icon
                    className={clsx(
                      'w-5 h-5 transition-all duration-200',
                      isActive ? 'text-neon-cyan' : 'group-hover:text-neon-cyan'
                    )}
                  />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* User */}
          <div className="p-4 border-t border-cyber-600/50">
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="w-full flex items-center gap-3 p-3 rounded-lg bg-cyber-700/30 border border-cyber-600/50 hover:border-neon-cyan/30 transition-colors cursor-pointer"
              >
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-neon-purple to-neon-cyan flex items-center justify-center">
                  <span className="text-sm font-bold text-cyber-900">{userInitial}</span>
                </div>
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium text-gray-200 truncate">{displayName}</p>
                  <p className="text-xs text-gray-500 font-mono truncate">{displayEmail}</p>
                </div>
                <div className="w-2 h-2 rounded-full bg-ai-active" />
              </button>

              {/* User menu dropdown */}
              {showUserMenu && (
                <>
                  <div
                    className="fixed inset-0 z-20"
                    onClick={() => setShowUserMenu(false)}
                  />
                  <div className="absolute bottom-full left-0 right-0 mb-2 bg-cyber-800/95 backdrop-blur-xl border border-cyber-600/50 rounded-lg shadow-xl z-30 overflow-hidden">
                    <div className="p-3 border-b border-cyber-600/50">
                      <p className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-1">
                        Signed in as
                      </p>
                      <p className="text-sm font-medium text-gray-200">{user?.username}</p>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-3 p-3 text-left hover:bg-cyber-700/50 transition-colors text-gray-300 hover:text-ai-error group"
                    >
                      <LogOut className="w-4 h-4 group-hover:text-ai-error" />
                      <span className="text-sm">Sign out</span>
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="pl-72">
        {/* Header */}
        <header className="sticky top-0 h-16 bg-cyber-800/90 backdrop-blur-xl border-b border-cyber-600/40 flex items-center justify-between px-8 z-10">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold text-gray-100">
              {navItems.find((item) => item.path === location.pathname)?.label || 'Dashboard'}
            </h2>
            <div className="h-6 w-px bg-cyber-600" />
            <span className="text-xs text-gray-500">
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
            <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-ai-active/10 border border-ai-active/20">
              <div className="w-2 h-2 rounded-full bg-ai-active" />
              <span className="text-sm text-ai-active">AI Active</span>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-8">{children}</main>
      </div>
    </div>
  );
};
