import React, { useEffect, useState } from 'react';
import { Card, CardHeader } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { MetricCard } from '@/components/common/MetricCard';
import {
  Users,
  Building2,
  AlertTriangle,
  CheckCircle,
  Clock,
  Loader2,
  RefreshCw,
  TrendingUp,
  ChevronDown,
  ChevronRight,
  Filter,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/common/Button';
import { ErrorDetailModal } from '@/components/errors/ErrorDetailModal';
import {
  formatErrorDateTime,
  ERROR_CATEGORIES,
} from '@/utils/errorDescriptions';
import { useData } from '@/contexts/DataContext';

interface RecentError {
  id: string;
  error_key: string;
  error_name: string;
  error_message: string;
  severity: string;
  status: string;
  category?: string;
  fix_strategy?: string;
  discovered_at: string;
  driver_name?: string;
  company_name?: string;
  error_metadata?: Record<string, any>;
}

export const Results: React.FC = () => {
  const {
    errorsByDriver,
    errorsByDriverLoading,
    refreshErrorsByDriver,
    getCacheAge,
  } = useData();

  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [expandedDrivers, setExpandedDrivers] = useState<Set<string>>(new Set());
  const [selectedError, setSelectedError] = useState<RecentError | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState<string | null>(null);

  useEffect(() => {
    const cacheAge = getCacheAge('errorsByDriver');
    if (cacheAge !== null) {
      setLastUpdate(new Date(Date.now() - cacheAge));
    }
  }, [errorsByDriver, getCacheAge]);

  const getSeverityBadge = (severity: string) => {
    const styles = {
      critical: 'bg-red-500/20 text-red-400 border-red-500/50',
      high: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
      medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
      low: 'bg-gray-500/20 text-gray-400 border-gray-500/50',
    };
    return styles[severity as keyof typeof styles] || styles.low;
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      pending: 'bg-yellow-500/20 text-yellow-400',
      fixing: 'bg-cyan-500/20 text-cyan-400',
      fixed: 'bg-green-500/20 text-green-400',
      failed: 'bg-red-500/20 text-red-400',
      ignored: 'bg-gray-500/20 text-gray-500',
    };
    return styles[status as keyof typeof styles] || 'bg-gray-500/20 text-gray-400';
  };

  const toggleDriverExpansion = (driverId: string) => {
    setExpandedDrivers((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(driverId)) {
        newSet.delete(driverId);
      } else {
        newSet.add(driverId);
      }
      return newSet;
    });
  };

  const expandAll = () => {
    setExpandedDrivers(new Set(errorsByDriver.map(d => d.driver_id)));
  };

  const collapseAll = () => {
    setExpandedDrivers(new Set());
  };

  const formatRelativeTime = (isoString: string): string => {
    return formatErrorDateTime(isoString).relative;
  };

  if (errorsByDriverLoading && errorsByDriver.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-500" />
      </div>
    );
  }

  const totalDrivers = errorsByDriver.length;
  const totalErrors = errorsByDriver.reduce((sum, r) => sum + r.total_errors, 0);
  const totalFixed = errorsByDriver.reduce((sum, r) => sum + r.by_status.fixed, 0);
  const totalPending = errorsByDriver.reduce((sum, r) => sum + r.by_status.pending, 0);
  const totalCritical = errorsByDriver.reduce((sum, r) => sum + r.by_severity.critical, 0);

  const filterErrors = (errors: RecentError[]): RecentError[] => {
    return errors.filter((error) => {
      if (filterSeverity && error.severity !== filterSeverity) return false;
      if (filterCategory && error.category !== filterCategory) return false;
      return true;
    });
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-7 h-7 text-cyan-400" />
            Результаты анализа
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Обновлено: {formatRelativeTime(lastUpdate.toISOString())}
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* Filters */}
          <select
            value={filterSeverity || ''}
            onChange={(e) => setFilterSeverity(e.target.value || null)}
            className="bg-cyber-700 border border-cyber-600 rounded-lg px-3 py-2 text-sm text-white"
          >
            <option value="">Все уровни</option>
            <option value="critical">Критичные</option>
            <option value="high">Высокие</option>
            <option value="medium">Средние</option>
            <option value="low">Низкие</option>
          </select>

          <select
            value={filterCategory || ''}
            onChange={(e) => setFilterCategory(e.target.value || null)}
            className="bg-cyber-700 border border-cyber-600 rounded-lg px-3 py-2 text-sm text-white"
          >
            <option value="">Все категории</option>
            {Object.entries(ERROR_CATEGORIES).map(([key, cat]) => (
              <option key={key} value={key}>
                {cat.name}
              </option>
            ))}
          </select>

          <div className="flex gap-1">
            <Button onClick={expandAll} variant="ghost" size="sm" title="Развернуть все">
              <ChevronDown className="w-4 h-4" />
            </Button>
            <Button onClick={collapseAll} variant="ghost" size="sm" title="Свернуть все">
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>

          <Button onClick={refreshErrorsByDriver} variant="secondary" size="sm">
            <RefreshCw className={`w-4 h-4 mr-2 ${errorsByDriverLoading ? 'animate-spin' : ''}`} />
            Обновить
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <MetricCard
          title="Водителей"
          value={totalDrivers}
          icon={Users}
          color="cyan"
        />
        <MetricCard
          title="Всего ошибок"
          value={totalErrors}
          icon={AlertTriangle}
          color="orange"
        />
        <MetricCard
          title="Критичных"
          value={totalCritical}
          icon={XCircle}
          color="red"
        />
        <MetricCard
          title="Ожидает"
          value={totalPending}
          icon={Clock}
          color="yellow"
        />
        <MetricCard
          title="Исправлено"
          value={totalFixed}
          icon={CheckCircle}
          color="green"
        />
      </div>

      {/* Driver Results */}
      {errorsByDriver.length === 0 ? (
        <Card variant="glass">
          <div className="text-center py-12">
            <Users className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg">Нет данных</p>
            <p className="text-gray-500 text-sm mt-2">
              Запустите сканирование для получения результатов
            </p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {errorsByDriver.map((driver) => {
            const filteredErrors = filterErrors(driver.recent_errors);
            const isExpanded = expandedDrivers.has(driver.driver_id);
            const hasErrors = filteredErrors.length > 0;

            return (
              <Card key={driver.driver_id} variant="glass" className="overflow-hidden">
                {/* Compact Driver Header */}
                <div
                  className="p-4 cursor-pointer hover:bg-cyber-700/30 transition-colors"
                  onClick={() => toggleDriverExpansion(driver.driver_id)}
                >
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      {/* Expand/Collapse Icon */}
                      <div className="flex-shrink-0">
                        {isExpanded ? (
                          <ChevronDown className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronRight className="w-5 h-5 text-gray-400" />
                        )}
                      </div>

                      {/* Driver Info */}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <Users className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                          <span className="font-semibold text-white truncate">
                            {driver.driver_name || 'Неизвестный водитель'}
                          </span>
                          <span className="text-gray-500">•</span>
                          <div className="flex items-center gap-1 text-gray-400 text-sm">
                            <Building2 className="w-3 h-3" />
                            <span className="truncate">{driver.company_name || 'N/A'}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Quick Stats Badges */}
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {driver.by_severity.critical > 0 && (
                        <span className="px-2 py-1 text-xs font-mono bg-red-500/20 text-red-400 rounded border border-red-500/30">
                          {driver.by_severity.critical} CRIT
                        </span>
                      )}
                      {driver.by_severity.high > 0 && (
                        <span className="px-2 py-1 text-xs font-mono bg-orange-500/20 text-orange-400 rounded border border-orange-500/30">
                          {driver.by_severity.high} HIGH
                        </span>
                      )}
                      <span className="px-2 py-1 text-xs font-mono bg-cyber-600 text-gray-300 rounded">
                        {driver.total_errors} всего
                      </span>
                      {driver.by_status.fixed > 0 && (
                        <span className="px-2 py-1 text-xs font-mono bg-green-500/20 text-green-400 rounded">
                          {driver.by_status.fixed} ✓
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="border-t border-cyber-600/50">
                    {/* Errors Table */}
                    {hasErrors ? (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="bg-cyber-700/50 text-gray-400 text-xs uppercase">
                              <th className="px-4 py-3 text-left font-medium">Уровень</th>
                              <th className="px-4 py-3 text-left font-medium">Тип ошибки</th>
                              <th className="px-4 py-3 text-left font-medium">Описание</th>
                              <th className="px-4 py-3 text-left font-medium">Статус</th>
                              <th className="px-4 py-3 text-left font-medium">Время</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-cyber-600/30">
                            {filteredErrors.map((error) => {
                              const dateTime = formatErrorDateTime(error.discovered_at);
                              return (
                                <tr
                                  key={error.id}
                                  onClick={() => setSelectedError({
                                    ...error,
                                    driver_name: driver.driver_name,
                                    company_name: driver.company_name,
                                  })}
                                  className="hover:bg-cyber-700/30 cursor-pointer transition-colors"
                                >
                                  <td className="px-4 py-3">
                                    <span className={`px-2 py-1 text-xs font-mono rounded border ${getSeverityBadge(error.severity)}`}>
                                      {error.severity.toUpperCase()}
                                    </span>
                                  </td>
                                  <td className="px-4 py-3">
                                    <div>
                                      <span className="text-white font-medium">{error.error_name}</span>
                                      <div className="text-xs text-gray-500 font-mono">{error.error_key}</div>
                                    </div>
                                  </td>
                                  <td className="px-4 py-3 max-w-xs">
                                    <p className="text-gray-400 truncate" title={error.error_message}>
                                      {error.error_message || '—'}
                                    </p>
                                  </td>
                                  <td className="px-4 py-3">
                                    <span className={`px-2 py-1 text-xs font-mono rounded ${getStatusBadge(error.status)}`}>
                                      {error.status}
                                    </span>
                                  </td>
                                  <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
                                    {dateTime.relative}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="p-8 text-center text-gray-500">
                        <Filter className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p>Нет ошибок по выбранным фильтрам</p>
                      </div>
                    )}

                    {/* Summary Bar */}
                    <div className="px-4 py-3 bg-cyber-700/30 border-t border-cyber-600/30 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-4 text-gray-400">
                        <span>По критичности:</span>
                        <span className="text-red-400">{driver.by_severity.critical} critical</span>
                        <span className="text-orange-400">{driver.by_severity.high} high</span>
                        <span className="text-yellow-400">{driver.by_severity.medium} medium</span>
                        <span className="text-gray-500">{driver.by_severity.low} low</span>
                      </div>
                      <div className="flex items-center gap-4 text-gray-400">
                        <span className="text-yellow-400">{driver.by_status.pending} pending</span>
                        <span className="text-cyan-400">{driver.by_status.fixing} fixing</span>
                        <span className="text-green-400">{driver.by_status.fixed} fixed</span>
                      </div>
                    </div>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* Error Detail Modal */}
      <ErrorDetailModal error={selectedError} onClose={() => setSelectedError(null)} />
    </div>
  );
};
