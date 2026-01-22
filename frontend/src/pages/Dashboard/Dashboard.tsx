import React, { useEffect, useState } from 'react';
import { Card, CardHeader } from '@/components/common/Card';
import { Badge, StatusBadge } from '@/components/common/Badge';
import { MetricCard } from '@/components/common/MetricCard';
import { AIStatusIndicator } from '@/components/common/AIStatusIndicator';
import { ProgressRing } from '@/components/common/ProgressRing';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Brain,
  Activity,
  Zap,
  Server,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { formatNumber, formatPercentage, formatRelativeTime } from '@/utils/format';

// Mock data for initial render (will be replaced by API)
const defaultStats = {
  total_errors: 0,
  errors_pending: 0,
  errors_fixing: 0,
  errors_fixed: 0,
  errors_failed: 0,
  fixes_today: 0,
  success_rate: 0,
  errors_by_severity: { critical: 0, high: 0, medium: 0, low: 0 },
};

const defaultConfig = {
  state: 'stopped',
  polling_interval_seconds: 300,
  dry_run_mode: false,
};

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState(defaultStats);
  const [recentErrors, setRecentErrors] = useState<any[]>([]);
  const [agentConfig, setAgentConfig] = useState(defaultConfig);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch agent status
        const configResponse = await fetch('http://localhost:8000/api/agent/status');
        if (configResponse.ok) {
          const configData = await configResponse.json();
          setAgentConfig(configData);
        }

        // Fetch error stats
        const statsResponse = await fetch('http://localhost:8000/api/errors/stats');
        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          setStats(statsData);
        }

        // Fetch recent errors
        const errorsResponse = await fetch('http://localhost:8000/api/errors?limit=5&offset=0');
        if (errorsResponse.ok) {
          const errorsData = await errorsResponse.json();
          setRecentErrors(errorsData.errors || []);
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // Refresh every 10 seconds
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  const getStatusFromState = (state: string): 'running' | 'paused' | 'stopped' | 'processing' => {
    if (state === 'running') return 'running';
    if (state === 'paused') return 'paused';
    if (state === 'processing') return 'processing';
    return 'stopped';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-500" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* AI Agent Status Banner */}
      <Card variant="hologram" glow="cyan">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            <AIStatusIndicator status={getStatusFromState(agentConfig.state)} size="md" />
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h2 className="text-2xl font-cyber font-bold text-gray-100">
                  AI AGENT
                </h2>
                <StatusBadge status={agentConfig.state === 'running' ? 'online' : 'offline'} />
                {agentConfig.dry_run_mode && (
                  <Badge variant="warning" glow>DRY RUN</Badge>
                )}
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-ai-processing" />
                  <span className="text-sm font-mono text-gray-400">
                    Monitoring: <span className="text-neon-cyan">ACTIVE</span>
                  </span>
                </div>
                <div className="h-4 w-px bg-cyber-600" />
                <span className="text-sm font-mono text-gray-500">
                  Polling every {agentConfig.polling_interval_seconds / 60} minutes
                </span>
              </div>
            </div>
          </div>

          <div className="text-right">
            <p className="text-xs font-mono text-gray-500 mb-1">SUCCESS RATE</p>
            <ProgressRing progress={stats.success_rate} size={80} strokeWidth={6} color="green" />
          </div>
        </div>
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Errors"
          value={formatNumber(stats.total_errors)}
          icon={AlertTriangle}
          color="red"
          trend={{ value: 12, isPositive: false }}
        />
        <MetricCard
          title="Fixed Today"
          value={formatNumber(stats.fixes_today)}
          icon={CheckCircle}
          color="green"
          trend={{ value: 15, isPositive: true }}
        />
        <MetricCard
          title="Pending"
          value={formatNumber(stats.errors_pending)}
          icon={Clock}
          color="orange"
        />
        <MetricCard
          title="AI Efficiency"
          value={formatPercentage(stats.success_rate)}
          icon={Brain}
          color="cyan"
          trend={{ value: 3, isPositive: true }}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Error Severity */}
        <Card variant="glass">
          <CardHeader
            title="ERROR DISTRIBUTION"
            subtitle="By severity level"
            icon={<AlertTriangle className="w-5 h-5" />}
          />
          <div className="space-y-4">
            {[
              { label: 'CRITICAL', count: stats.errors_by_severity?.critical || 0, color: 'bg-ai-error', width: `${((stats.errors_by_severity?.critical || 0) / (stats.total_errors || 1)) * 100}%` },
              { label: 'HIGH', count: stats.errors_by_severity?.high || 0, color: 'bg-neon-orange', width: `${((stats.errors_by_severity?.high || 0) / (stats.total_errors || 1)) * 100}%` },
              { label: 'MEDIUM', count: stats.errors_by_severity?.medium || 0, color: 'bg-ai-processing', width: `${((stats.errors_by_severity?.medium || 0) / (stats.total_errors || 1)) * 100}%` },
              { label: 'LOW', count: stats.errors_by_severity?.low || 0, color: 'bg-gray-500', width: `${((stats.errors_by_severity?.low || 0) / (stats.total_errors || 1)) * 100}%` },
            ].map((item) => (
              <div key={item.label} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-mono text-gray-400">{item.label}</span>
                  <span className="text-sm font-mono text-gray-200">{item.count}</span>
                </div>
                <div className="h-2 bg-cyber-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${item.color} rounded-full transition-all duration-1000`}
                    style={{ width: item.width }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* System Health */}
        <Card variant="glass">
          <CardHeader
            title="SYSTEM HEALTH"
            subtitle="Real-time metrics"
            icon={<Server className="w-5 h-5" />}
          />
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <ProgressRing progress={78} size={80} strokeWidth={5} color="cyan" label="CPU" />
            </div>
            <div className="text-center">
              <ProgressRing progress={45} size={80} strokeWidth={5} color="green" label="MEMORY" />
            </div>
            <div className="text-center">
              <ProgressRing progress={23} size={80} strokeWidth={5} color="purple" label="NETWORK" />
            </div>
          </div>

          {/* Status Distribution */}
          <div className="mt-6 pt-6 border-t border-cyber-600/50">
            <p className="text-xs font-mono text-gray-500 mb-4">ERROR STATUS</p>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-mono text-gray-400">Pending</span>
                <div className="flex items-center gap-3">
                  <div className="w-32 h-1.5 bg-cyber-700 rounded-full overflow-hidden">
                    <div className="h-full bg-ai-warning rounded-full" style={{ width: `${(stats.errors_pending / (stats.total_errors || 1)) * 100}%` }} />
                  </div>
                  <span className="text-sm font-mono text-ai-warning w-8 text-right">{stats.errors_pending}</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-mono text-gray-400">Fixing</span>
                <div className="flex items-center gap-3">
                  <div className="w-32 h-1.5 bg-cyber-700 rounded-full overflow-hidden">
                    <div className="h-full bg-ai-processing rounded-full" style={{ width: `${(stats.errors_fixing / (stats.total_errors || 1)) * 100}%` }} />
                  </div>
                  <span className="text-sm font-mono text-ai-processing w-8 text-right">{stats.errors_fixing}</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-mono text-gray-400">Fixed</span>
                <div className="flex items-center gap-3">
                  <div className="w-32 h-1.5 bg-cyber-700 rounded-full overflow-hidden">
                    <div className="h-full bg-ai-active rounded-full" style={{ width: `${(stats.errors_fixed / (stats.total_errors || 1)) * 100}%` }} />
                  </div>
                  <span className="text-sm font-mono text-ai-active w-8 text-right">{stats.errors_fixed}</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-mono text-gray-400">Failed</span>
                <div className="flex items-center gap-3">
                  <div className="w-32 h-1.5 bg-cyber-700 rounded-full overflow-hidden">
                    <div className="h-full bg-ai-error rounded-full" style={{ width: `${(stats.errors_failed / (stats.total_errors || 1)) * 100}%` }} />
                  </div>
                  <span className="text-sm font-mono text-ai-error w-8 text-right">{stats.errors_failed}</span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Real-time Activity */}
      <Card variant="glass">
        <CardHeader
          title="REAL-TIME ACTIVITY"
          subtitle="Latest AI agent actions"
          icon={<Zap className="w-5 h-5" />}
        />
        <div className="space-y-3">
          {[
            { time: '2m ago', action: 'Error Detected', detail: 'odometerError - John Smith', type: 'error' },
            { time: '5m ago', action: 'Fix Proposed', detail: 'twoIdenticalStatusesError', type: 'processing' },
            { time: '10m ago', action: 'Fix Applied', detail: 'noPowerUpError - Mike Johnson', type: 'success' },
            { time: '15m ago', action: 'Scan Complete', detail: '150 logs checked, 2 errors found', type: 'info' },
          ].map((log, i) => (
            <div
              key={i}
              className="flex items-center gap-4 p-4 rounded-lg bg-cyber-800/50 border border-cyber-600/30 hover:border-neon-cyan/30 transition-colors"
            >
              <div
                className={`
                  w-2 h-2 rounded-full
                  ${log.type === 'error' ? 'bg-ai-error' : ''}
                  ${log.type === 'processing' ? 'bg-ai-processing animate-pulse' : ''}
                  ${log.type === 'success' ? 'bg-ai-active' : ''}
                  ${log.type === 'info' ? 'bg-neon-blue' : ''}
                `}
              />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-200">{log.action}</p>
                <p className="text-xs font-mono text-gray-500">{log.detail}</p>
              </div>
              <span className="text-xs font-mono text-gray-500">{log.time}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Recent Errors Table */}
      <Card variant="glass" padding="none">
        <div className="p-6 border-b border-cyber-600/30">
          <CardHeader
            title="RECENT ERRORS"
            subtitle="Latest detected errors from monitoring"
            icon={<AlertCircle className="w-5 h-5" />}
            className="mb-0"
          />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-cyber-600/30">
                <th className="px-6 py-4 text-left text-xs font-mono text-neon-cyan uppercase tracking-widest bg-cyber-800/50">Driver</th>
                <th className="px-6 py-4 text-left text-xs font-mono text-neon-cyan uppercase tracking-widest bg-cyber-800/50">Error Type</th>
                <th className="px-6 py-4 text-left text-xs font-mono text-neon-cyan uppercase tracking-widest bg-cyber-800/50">Message</th>
                <th className="px-6 py-4 text-left text-xs font-mono text-neon-cyan uppercase tracking-widest bg-cyber-800/50">Severity</th>
                <th className="px-6 py-4 text-left text-xs font-mono text-neon-cyan uppercase tracking-widest bg-cyber-800/50">Status</th>
                <th className="px-6 py-4 text-left text-xs font-mono text-neon-cyan uppercase tracking-widest bg-cyber-800/50">Discovered</th>
              </tr>
            </thead>
            <tbody>
              {recentErrors.map((error, index) => (
                <tr
                  key={error.id}
                  className={`
                    border-b border-cyber-600/20 transition-all duration-200
                    cursor-pointer hover:bg-neon-cyan/5
                    ${index % 2 === 0 ? 'bg-cyber-800/20' : 'bg-transparent'}
                  `}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-200">{error.driver_name}</div>
                      <div className="text-xs text-gray-500 font-mono">{error.company_name}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm font-mono text-gray-300">{error.error_name}</span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-400 max-w-md truncate">{error.error_message}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge
                      variant={
                        error.severity === 'critical' || error.severity === 'high'
                          ? 'danger'
                          : error.severity === 'medium'
                          ? 'warning'
                          : 'default'
                      }
                      glow={error.severity === 'critical' || error.severity === 'high'}
                    >
                      {error.severity}
                    </Badge>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge
                      variant={
                        error.status === 'fixed'
                          ? 'success'
                          : error.status === 'fixing'
                          ? 'processing'
                          : error.status === 'failed'
                          ? 'danger'
                          : 'warning'
                      }
                      pulse={error.status === 'fixing'}
                    >
                      {error.status}
                    </Badge>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">
                    {formatRelativeTime(error.discovered_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
