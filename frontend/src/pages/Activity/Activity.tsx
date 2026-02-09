import React, { useEffect, useState } from 'react';
import { Card, CardHeader } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
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
  Play,
  Building2,
  Users,
  FileSearch,
  Microscope,
  XCircle,
} from 'lucide-react';
import { formatRelativeTime } from '@/utils/format';
import { Button } from '@/components/common/Button';
import { useData } from '@/contexts/DataContext';

export const Activity: React.FC = () => {
  // Use global data context
  const {
    errorStats,
    errorStatsLoading,
    recentErrors,
    recentErrorsLoading,
    recentFixes,
    recentFixesLoading,
    refreshErrorStats,
    refreshRecentErrors,
    refreshRecentFixes,
    getCacheAge,
    scanActivities,
  } = useData();

  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Update last update time based on cache age
  useEffect(() => {
    const cacheAge = getCacheAge('errorStats');
    if (cacheAge !== null) {
      setLastUpdate(new Date(Date.now() - cacheAge));
    }
  }, [errorStats, getCacheAge]);

  const handleRefresh = async () => {
    await Promise.all([
      refreshErrorStats(),
      refreshRecentErrors(),
      refreshRecentFixes(),
    ]);
  };

  const loading = errorStatsLoading || recentErrorsLoading || recentFixesLoading;

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
      running: 'text-cyan-400',
      completed: 'text-green-400',
    };
    return colors[status as keyof typeof colors] || 'text-gray-400';
  };

  const getScanTypeInfo = (type: string) => {
    switch (type) {
      case 'smart_analyze':
        return { label: 'Smart Analyze', icon: Microscope, color: 'text-purple-400' };
      case 'full_scan':
        return { label: 'Полное сканирование', icon: FileSearch, color: 'text-orange-400' };
      case 'log_scan':
        return { label: 'Сканирование логов', icon: FileSearch, color: 'text-blue-400' };
      default:
        return { label: 'Сканирование', icon: Play, color: 'text-gray-400' };
    }
  };

  if (loading && recentErrors.length === 0) {
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

        <Button onClick={handleRefresh} variant="secondary" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" />
          Обновить
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Всего ошибок"
          value={errorStats.total_errors}
          icon={AlertTriangle}
          color="cyan"
        />
        <MetricCard
          title="В ожидании"
          value={errorStats.errors_pending}
          icon={Clock}
          color="orange"
        />
        <MetricCard
          title="Исправлено"
          value={errorStats.errors_fixed}
          icon={CheckCircle}
          color="green"
        />
        <MetricCard
          title="Процент успеха"
          value={`${errorStats.success_rate}%`}
          icon={Zap}
          color="cyan"
        />
      </div>

      {/* Scan Activities - NEW SECTION */}
      <Card variant="glass">
        <CardHeader
          title="ИСТОРИЯ СКАНИРОВАНИЙ"
          subtitle={`${scanActivities.length} операций`}
          icon={<Play className="w-5 h-5" />}
        />
        <div className="space-y-2">
          {scanActivities.length === 0 ? (
            <p className="text-center text-gray-500 py-8 text-sm">
              Нет истории сканирований. Запустите сканирование на вкладке Control.
            </p>
          ) : (
            scanActivities.slice(0, 10).map((activity) => {
              const typeInfo = getScanTypeInfo(activity.type);
              const TypeIcon = typeInfo.icon;

              return (
                <div
                  key={activity.id}
                  className={`p-4 rounded-lg border ${
                    activity.status === 'running'
                      ? 'bg-cyan-900/20 border-cyan-500/50'
                      : activity.status === 'completed'
                      ? 'bg-green-900/20 border-green-500/30'
                      : 'bg-red-900/20 border-red-500/30'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      {/* Type and Status */}
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <TypeIcon className={`w-4 h-4 ${typeInfo.color}`} />
                        <span className={`text-sm font-semibold ${typeInfo.color}`}>
                          {typeInfo.label}
                        </span>
                        <span className="text-gray-500">•</span>
                        <span className={`text-xs font-mono ${getStatusColor(activity.status)}`}>
                          {activity.status === 'running' && (
                            <Loader2 className="w-3 h-3 inline animate-spin mr-1" />
                          )}
                          {activity.status === 'completed' && (
                            <CheckCircle className="w-3 h-3 inline mr-1" />
                          )}
                          {activity.status === 'failed' && (
                            <XCircle className="w-3 h-3 inline mr-1" />
                          )}
                          {activity.status.toUpperCase()}
                        </span>
                      </div>

                      {/* Company and Drivers */}
                      <div className="flex items-center gap-4 text-sm text-gray-400">
                        {activity.companyName && (
                          <div className="flex items-center gap-1">
                            <Building2 className="w-3 h-3" />
                            <span>{activity.companyName}</span>
                          </div>
                        )}
                        <div className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          <span>{activity.driverCount} водителей</span>
                        </div>
                      </div>

                      {/* Message */}
                      {activity.message && (
                        <p className="text-xs text-gray-500 mt-2">
                          {activity.message}
                        </p>
                      )}
                    </div>

                    {/* Time */}
                    <div className="text-right flex-shrink-0">
                      <span className="text-xs text-gray-500 whitespace-nowrap">
                        {formatRelativeTime(activity.startedAt)}
                      </span>
                      {activity.completedAt && (
                        <span className="text-xs text-gray-600 block mt-1">
                          {Math.round(
                            (new Date(activity.completedAt).getTime() -
                              new Date(activity.startedAt).getTime()) /
                              1000
                          )}
                          s
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </Card>

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
              { label: 'CRITICAL', count: errorStats.errors_by_severity?.critical || 0, color: 'bg-red-500' },
              { label: 'HIGH', count: errorStats.errors_by_severity?.high || 0, color: 'bg-orange-500' },
              { label: 'MEDIUM', count: errorStats.errors_by_severity?.medium || 0, color: 'bg-yellow-500' },
              { label: 'LOW', count: errorStats.errors_by_severity?.low || 0, color: 'bg-gray-500' },
            ].map((item) => (
              <div key={item.label} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-mono text-gray-400">{item.label}</span>
                  <span className="text-sm font-mono text-gray-200">{item.count}</span>
                </div>
                <div className="h-2 bg-cyber-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${item.color} rounded-full transition-all`}
                    style={{ width: `${((item.count) / (errorStats.total_errors || 1)) * 100}%` }}
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
              { label: 'Pending', count: errorStats.errors_pending, color: 'bg-yellow-500' },
              { label: 'Fixing', count: errorStats.errors_fixing, color: 'bg-cyan-500' },
              { label: 'Fixed', count: errorStats.errors_fixed, color: 'bg-green-500' },
              { label: 'Failed', count: errorStats.errors_failed, color: 'bg-red-500' },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between">
                <span className="text-sm font-mono text-gray-400">{item.label}</span>
                <div className="flex items-center gap-3">
                  <div className="w-32 h-1.5 bg-cyber-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${item.color} rounded-full`}
                      style={{ width: `${(item.count / (errorStats.total_errors || 1)) * 100}%` }}
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
