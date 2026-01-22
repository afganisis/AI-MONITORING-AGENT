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
} from 'lucide-react';
import { formatRelativeTime } from '@/utils/format';
import { Button } from '@/components/common/Button';

interface ErrorByDriver {
  driver_id: string;
  driver_name: string;
  company_id: string;
  company_name: string;
  total_errors: number;
  by_severity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  by_status: {
    pending: number;
    fixing: number;
    fixed: number;
    failed: number;
  };
  recent_errors: Array<{
    id: string;
    error_key: string;
    error_name: string;
    error_message: string;
    severity: string;
    status: string;
    discovered_at: string;
  }>;
}

export const Results: React.FC = () => {
  const [results, setResults] = useState<ErrorByDriver[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchResults = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/errors/by-driver');
      if (response.ok) {
        const data = await response.json();
        setResults(data.results || []);
      }
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching results:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
    const interval = setInterval(fetchResults, 15000); // Refresh every 15 seconds
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

  const totalDrivers = results.length;
  const totalErrors = results.reduce((sum, r) => sum + r.total_errors, 0);
  const totalFixed = results.reduce((sum, r) => sum + r.by_status.fixed, 0);
  const totalPending = results.reduce((sum, r) => sum + r.by_status.pending, 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-7 h-7 text-cyan-400" />
            Результаты по водителям
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Последнее обновление: {formatRelativeTime(lastUpdate.toISOString())}
          </p>
        </div>

        <Button onClick={fetchResults} variant="secondary" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" />
          Обновить
        </Button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
          title="В ожидании"
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
      {results.length === 0 ? (
        <Card variant="glass">
          <div className="text-center py-12">
            <Users className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg">Нет данных</p>
            <p className="text-gray-500 text-sm mt-2">
              Выберите водителей и запустите агента
            </p>
          </div>
        </Card>
      ) : (
        <div className="space-y-6">
          {results.map((driver) => (
            <Card key={driver.driver_id} variant="glass">
              <CardHeader
                title={driver.driver_name || 'Неизвестный водитель'}
                subtitle={
                  <div className="flex items-center gap-2 mt-1">
                    <Building2 className="w-4 h-4" />
                    <span>{driver.company_name}</span>
                  </div>
                }
                icon={<Users className="w-5 h-5" />}
              />

              {/* Driver Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-cyber-700 rounded-lg p-3 border border-cyber-600">
                  <div className="text-xs text-gray-400 mb-1">Всего ошибок</div>
                  <div className="text-xl font-bold text-white">{driver.total_errors}</div>
                </div>
                <div className="bg-yellow-900/20 rounded-lg p-3 border border-yellow-500/30">
                  <div className="text-xs text-yellow-400 mb-1">В ожидании</div>
                  <div className="text-xl font-bold text-yellow-400">{driver.by_status.pending}</div>
                </div>
                <div className="bg-cyan-900/20 rounded-lg p-3 border border-cyan-500/30">
                  <div className="text-xs text-cyan-400 mb-1">Исправляется</div>
                  <div className="text-xl font-bold text-cyan-400">{driver.by_status.fixing}</div>
                </div>
                <div className="bg-green-900/20 rounded-lg p-3 border border-green-500/30">
                  <div className="text-xs text-green-400 mb-1">Исправлено</div>
                  <div className="text-xl font-bold text-green-400">{driver.by_status.fixed}</div>
                </div>
              </div>

              {/* Severity Distribution */}
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">По критичности</h3>
                <div className="grid grid-cols-4 gap-2">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-400">{driver.by_severity.critical}</div>
                    <div className="text-xs text-gray-500 uppercase">Critical</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-400">{driver.by_severity.high}</div>
                    <div className="text-xs text-gray-500 uppercase">High</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-400">{driver.by_severity.medium}</div>
                    <div className="text-xs text-gray-500 uppercase">Medium</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-400">{driver.by_severity.low}</div>
                    <div className="text-xs text-gray-500 uppercase">Low</div>
                  </div>
                </div>
              </div>

              {/* Recent Errors */}
              {driver.recent_errors.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-300 mb-3">Последние ошибки</h3>
                  <div className="space-y-2">
                    {driver.recent_errors.slice(0, 5).map((error) => (
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
                            <h4 className="text-sm font-semibold text-white mb-1">
                              {error.error_name}
                            </h4>
                            {error.error_message && (
                              <p className="text-xs text-gray-400 truncate">
                                {error.error_message}
                              </p>
                            )}
                          </div>
                          <span className="text-xs text-gray-500 whitespace-nowrap ml-3">
                            {formatRelativeTime(error.discovered_at)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
