import React, { useEffect, useState } from 'react';
import { Card, CardHeader } from '@/components/common/Card';
import { Badge, StatusBadge } from '@/components/common/Badge';
import { MetricCard } from '@/components/common/MetricCard';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Activity as ActivityIcon,
  Zap,
  AlertCircle,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { formatRelativeTime } from '@/utils/format';
import { Button } from '@/components/common/Button';

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

interface Error {
  id: string;
  error_key: string;
  severity: string;
  status: string;
  driver_name: string;
  company_name: string;
  created_at: string;
  error_message?: string;
}

interface Fix {
  id: string;
  error_id: string;
  status: string;
  started_at: string;
  completed_at?: string;
  error_key: string;
  driver_name: string;
  result_message?: string;
}

export const Activity: React.FC = () => {
  const [stats, setStats] = useState(defaultStats);
  const [recentErrors, setRecentErrors] = useState<Error[]>([]);
  const [recentFixes, setRecentFixes] = useState<Fix[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchData = async () => {
    try {
      // Fetch error stats
      const statsResponse = await fetch('http://localhost:8000/api/errors/stats');
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();

        // Transform stats to match expected format
        const transformedStats = {
          total_errors: statsData.total_errors || 0,
          errors_pending: statsData.by_status?.pending || 0,
          errors_fixing: statsData.by_status?.fixing || 0,
          errors_fixed: statsData.by_status?.fixed || 0,
          errors_failed: statsData.by_status?.failed || 0,
          fixes_today: 0, // TODO: implement
          success_rate: statsData.total_errors > 0
            ? Math.round(((statsData.by_status?.fixed || 0) / statsData.total_errors) * 100)
            : 0,
          errors_by_severity: {
            critical: statsData.by_severity?.critical || 0,
            high: statsData.by_severity?.high || 0,
            medium: statsData.by_severity?.medium || 0,
            low: statsData.by_severity?.low || 0,
          },
        };
        setStats(transformedStats);
      }

      // Fetch recent errors - use page and page_size parameters
      const errorsResponse = await fetch('http://localhost:8000/api/errors?page=1&page_size=10');
      if (errorsResponse.ok) {
        const errorsData = await errorsResponse.json();
        setRecentErrors(errorsData.errors || []);
      }

      // Fetch recent fixes
      const fixesResponse = await fetch('http://localhost:8000/api/fixes?page=1&page_size=10');
      if (fixesResponse.ok) {
        const fixesData = await fixesResponse.json();
        setRecentFixes(fixesData.fixes || []);
      }

      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching activity data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const getSeverityColor = (severity: string) => {
    const colors = {
      critical: 'text-red-400 bg-red-900/30 border-red-500',
      high: 'text-orange-400 bg-orange-900/30 border-orange-500',
      medium: 'text-yellow-400 bg-yellow-900/30 border-yellow-500',
      low: 'text-gray-400 bg-gray-900/30 border-gray-500',
    };
    return colors[severity as keyof typeof colors] || colors.low;
  };

  const getStatusColor = (status: string) => {
    const colors = {
      pending: 'text-yellow-400',
      fixing: 'text-cyan-400',
      fixed: 'text-green-400',
      failed: 'text-red-400',
      success: 'text-green-400',
    };
    return colors[status as keyof typeof colors] || 'text-gray-400';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-500" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ActivityIcon className="w-7 h-7 text-cyan-400" />
            Активность агента
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Последнее обновление: {formatRelativeTime(lastUpdate.toISOString())}
          </p>
        </div>

        <Button onClick={fetchData} variant="secondary" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" />
          Обновить
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Всего ошибок"
          value={stats.total_errors}
          icon={AlertTriangle}
          color="cyan"
        />
        <MetricCard
          title="В ожидании"
          value={stats.errors_pending}
          icon={Clock}
          color="orange"
        />
        <MetricCard
          title="Исправлено"
          value={stats.errors_fixed}
          icon={CheckCircle}
          color="green"
        />
        <MetricCard
          title="Процент успеха"
          value={`${stats.success_rate}%`}
          icon={Zap}
          color="cyan"
        />
      </div>

      {/* Distribution Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Distribution */}
        <Card variant="glass">
          <CardHeader
            title="ПО КРИТИЧНОСТИ"
            subtitle="Распределение ошибок"
            icon={<AlertTriangle className="w-5 h-5" />}
          />
          <div className="space-y-3">
            {[
              { label: 'CRITICAL', count: stats.errors_by_severity?.critical || 0, color: 'bg-red-500' },
              { label: 'HIGH', count: stats.errors_by_severity?.high || 0, color: 'bg-orange-500' },
              { label: 'MEDIUM', count: stats.errors_by_severity?.medium || 0, color: 'bg-yellow-500' },
              { label: 'LOW', count: stats.errors_by_severity?.low || 0, color: 'bg-gray-500' },
            ].map((item) => (
              <div key={item.label} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-mono text-gray-400">{item.label}</span>
                  <span className="text-sm font-mono text-gray-200">{item.count}</span>
                </div>
                <div className="h-2 bg-cyber-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${item.color} rounded-full transition-all`}
                    style={{ width: `${((item.count) / (stats.total_errors || 1)) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Status Distribution */}
        <Card variant="glass">
          <CardHeader
            title="ПО СТАТУСУ"
            subtitle="Текущее состояние"
            icon={<ActivityIcon className="w-5 h-5" />}
          />
          <div className="space-y-3">
            {[
              { label: 'Pending', count: stats.errors_pending, color: 'bg-yellow-500' },
              { label: 'Fixing', count: stats.errors_fixing, color: 'bg-cyan-500' },
              { label: 'Fixed', count: stats.errors_fixed, color: 'bg-green-500' },
              { label: 'Failed', count: stats.errors_failed, color: 'bg-red-500' },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between">
                <span className="text-sm font-mono text-gray-400">{item.label}</span>
                <div className="flex items-center gap-3">
                  <div className="w-32 h-1.5 bg-cyber-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${item.color} rounded-full`}
                      style={{ width: `${(item.count / (stats.total_errors || 1)) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-mono text-gray-200 w-8 text-right">{item.count}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Recent Errors */}
      <Card variant="glass">
        <CardHeader
          title="ПОСЛЕДНИЕ ОШИБКИ"
          subtitle={`${recentErrors.length} найдено`}
          icon={<AlertCircle className="w-5 h-5" />}
        />
        <div className="space-y-2">
          {recentErrors.length === 0 ? (
            <p className="text-center text-gray-500 py-8 text-sm">Ошибок нет</p>
          ) : (
            recentErrors.map((error) => (
              <div
                key={error.id}
                className={`p-3 rounded-lg border ${getSeverityColor(error.severity)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant={error.severity as any} className="text-xs">
                        {error.severity.toUpperCase()}
                      </Badge>
                      <span className={`text-xs font-mono ${getStatusColor(error.status)}`}>
                        {error.status}
                      </span>
                    </div>
                    <h3 className="text-sm font-semibold text-white mb-1">
                      {error.error_key}
                    </h3>
                    <p className="text-xs text-gray-400">
                      {error.driver_name} • {error.company_name}
                    </p>
                    {error.error_message && (
                      <p className="text-xs text-gray-500 mt-1 truncate">
                        {error.error_message}
                      </p>
                    )}
                  </div>
                  <span className="text-xs text-gray-500 whitespace-nowrap ml-3">
                    {formatRelativeTime(error.created_at)}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>

      {/* Recent Fixes */}
      <Card variant="glass">
        <CardHeader
          title="ПОСЛЕДНИЕ ИСПРАВЛЕНИЯ"
          subtitle={`${recentFixes.length} попыток`}
          icon={<Zap className="w-5 h-5" />}
        />
        <div className="space-y-2">
          {recentFixes.length === 0 ? (
            <p className="text-center text-gray-500 py-8 text-sm">Исправлений нет</p>
          ) : (
            recentFixes.map((fix) => (
              <div
                key={fix.id}
                className="p-3 rounded-lg bg-cyber-700 border border-cyber-600"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-mono font-semibold ${getStatusColor(fix.status)}`}>
                        {fix.status.toUpperCase()}
                      </span>
                    </div>
                    <h3 className="text-sm font-semibold text-white mb-1">
                      {fix.error_key}
                    </h3>
                    <p className="text-xs text-gray-400">
                      {fix.driver_name}
                    </p>
                    {fix.result_message && (
                      <p className="text-xs text-gray-500 mt-1">
                        {fix.result_message}
                      </p>
                    )}
                  </div>
                  <div className="text-right ml-3">
                    <span className="text-xs text-gray-500 whitespace-nowrap block">
                      {formatRelativeTime(fix.started_at)}
                    </span>
                    {fix.completed_at && fix.started_at && (
                      <span className="text-xs text-gray-600 whitespace-nowrap block mt-1">
                        {Math.round((new Date(fix.completed_at).getTime() - new Date(fix.started_at).getTime()) / 1000)}s
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
};
