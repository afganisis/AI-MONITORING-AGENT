import React from 'react';
import { Card, CardHeader } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { AlertTriangle, CheckCircle, Clock, TrendingUp, AlertCircle } from 'lucide-react';
import { mockAgentStats, mockErrors, mockAgentConfig } from '@/data/mockData';
import { formatNumber, formatPercentage, formatRelativeTime, getSeverityColor, getStatusColor } from '@/utils/format';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  iconColor: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, iconColor, trend }) => {
  return (
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
          {trend && (
            <div className="flex items-center mt-2">
              <TrendingUp className={`w-4 h-4 mr-1 ${trend.isPositive ? 'text-success-600' : 'text-danger-600'}`} />
              <span className={`text-sm font-medium ${trend.isPositive ? 'text-success-600' : 'text-danger-600'}`}>
                {trend.value}%
              </span>
              <span className="text-sm text-gray-500 ml-1">vs yesterday</span>
            </div>
          )}
        </div>
        <div className={`w-12 h-12 rounded-lg ${iconColor} flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </Card>
  );
};

export const Dashboard: React.FC = () => {
  const stats = mockAgentStats;
  const recentErrors = mockErrors.slice(0, 5);
  const agentConfig = mockAgentConfig;

  return (
    <div className="space-y-6">
      {/* Agent Status Banner */}
      <Card padding="sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${agentConfig.state === 'running' ? 'bg-success-500 animate-pulse' : 'bg-gray-400'}`}></div>
              <span className="text-lg font-semibold text-gray-900">
                Agent Status: <span className="text-success-600">{agentConfig.state.toUpperCase()}</span>
              </span>
            </div>
            {agentConfig.dry_run_mode && (
              <Badge variant="warning">Dry Run Mode</Badge>
            )}
          </div>
          <div className="text-sm text-gray-600">
            Polling every {agentConfig.polling_interval_seconds / 60} minutes
          </div>
        </div>
      </Card>

      {/* Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Errors"
          value={formatNumber(stats.total_errors)}
          icon={AlertTriangle}
          iconColor="bg-danger-500"
          trend={{ value: 12, isPositive: false }}
        />
        <StatCard
          title="Fixed Today"
          value={formatNumber(stats.fixes_today)}
          icon={CheckCircle}
          iconColor="bg-success-500"
          trend={{ value: 15, isPositive: true }}
        />
        <StatCard
          title="Pending"
          value={formatNumber(stats.errors_pending)}
          icon={Clock}
          iconColor="bg-warning-500"
        />
        <StatCard
          title="Success Rate"
          value={formatPercentage(stats.success_rate)}
          icon={TrendingUp}
          iconColor="bg-primary-500"
          trend={{ value: 3, isPositive: true }}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Errors by Severity */}
        <Card>
          <CardHeader title="Errors by Severity" />
          <div className="space-y-4">
            {Object.entries(stats.errors_by_severity).map(([severity, count]) => (
              <div key={severity} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Badge variant={severity === 'critical' || severity === 'high' ? 'danger' : severity === 'medium' ? 'warning' : 'default'}>
                    {severity}
                  </Badge>
                  <div className="flex-1 bg-gray-200 rounded-full h-2 w-48">
                    <div
                      className={`h-2 rounded-full ${
                        severity === 'critical' ? 'bg-danger-500' :
                        severity === 'high' ? 'bg-warning-500' :
                        severity === 'medium' ? 'bg-blue-500' : 'bg-gray-400'
                      }`}
                      style={{ width: `${(count / stats.total_errors) * 100}%` }}
                    ></div>
                  </div>
                </div>
                <span className="text-sm font-semibold text-gray-900">{count}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Error Status Distribution */}
        <Card>
          <CardHeader title="Error Status" />
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600">Pending</span>
              <div className="flex items-center space-x-2">
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div className="bg-warning-500 h-2 rounded-full" style={{ width: `${(stats.errors_pending / stats.total_errors) * 100}%` }}></div>
                </div>
                <span className="text-sm font-semibold text-gray-900 w-8 text-right">{stats.errors_pending}</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600">Fixing</span>
              <div className="flex items-center space-x-2">
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${(stats.errors_fixing / stats.total_errors) * 100}%` }}></div>
                </div>
                <span className="text-sm font-semibold text-gray-900 w-8 text-right">{stats.errors_fixing}</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600">Fixed</span>
              <div className="flex items-center space-x-2">
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div className="bg-success-500 h-2 rounded-full" style={{ width: `${(stats.errors_fixed / stats.total_errors) * 100}%` }}></div>
                </div>
                <span className="text-sm font-semibold text-gray-900 w-8 text-right">{stats.errors_fixed}</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600">Failed</span>
              <div className="flex items-center space-x-2">
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div className="bg-danger-500 h-2 rounded-full" style={{ width: `${(stats.errors_failed / stats.total_errors) * 100}%` }}></div>
                </div>
                <span className="text-sm font-semibold text-gray-900 w-8 text-right">{stats.errors_failed}</span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent Errors */}
      <Card>
        <CardHeader
          title="Recent Errors"
          subtitle="Latest detected errors from monitoring"
        />
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Driver</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Error Type</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Message</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Severity</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Discovered</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {recentErrors.map((error) => (
                <tr key={error.id} className="hover:bg-gray-50 cursor-pointer">
                  <td className="px-4 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{error.driver_name}</div>
                      <div className="text-xs text-gray-500">{error.company_name}</div>
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{error.error_name}</div>
                  </td>
                  <td className="px-4 py-4">
                    <div className="text-sm text-gray-600 max-w-md truncate">{error.error_message}</div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <Badge className={getSeverityColor(error.severity)}>
                      {error.severity}
                    </Badge>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <Badge className={getStatusColor(error.status)}>
                      {error.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
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
