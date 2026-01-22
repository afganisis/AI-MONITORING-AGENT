import React, { useState, useEffect } from 'react';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { Search, Filter, Download, RefreshCw, Loader2 } from 'lucide-react';
import { ErrorRecord, ErrorStatus, ErrorSeverity } from '@/types';
import { formatDate, formatRelativeTime, getSeverityColor, getStatusColor } from '@/utils/format';

export const ErrorList: React.FC = () => {
  const [errors, setErrors] = useState<ErrorRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSeverities, setSelectedSeverities] = useState<ErrorSeverity[]>([]);
  const [selectedStatuses, setSelectedStatuses] = useState<ErrorStatus[]>([]);

  useEffect(() => {
    fetchErrors();
  }, []);

  const fetchErrors = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/errors?limit=100&offset=0');
      if (response.ok) {
        const data = await response.json();
        setErrors(data.errors || []);
      }
    } catch (error) {
      console.error('Error fetching errors:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredErrors = errors.filter((error) => {
    const matchesSearch =
      searchTerm === '' ||
      error.driver_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      error.error_message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      error.error_name.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesSeverity =
      selectedSeverities.length === 0 || selectedSeverities.includes(error.severity);

    const matchesStatus =
      selectedStatuses.length === 0 || selectedStatuses.includes(error.status);

    return matchesSearch && matchesSeverity && matchesStatus;
  });

  const toggleSeverity = (severity: ErrorSeverity) => {
    setSelectedSeverities((prev) =>
      prev.includes(severity) ? prev.filter((s) => s !== severity) : [...prev, severity]
    );
  };

  const toggleStatus = (status: ErrorStatus) => {
    setSelectedStatuses((prev) =>
      prev.includes(status) ? prev.filter((s) => s !== status) : [...prev, status]
    );
  };

  return (
    <div className="space-y-6">
      {/* Filters Bar */}
      <Card padding="sm">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by driver, error type, or message..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-3">
            <Button variant="ghost" size="sm" onClick={fetchErrors} disabled={loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="ghost" size="sm">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="mt-4 flex flex-wrap gap-4">
          {/* Severity Filter */}
          <div>
            <span className="text-sm font-medium text-gray-700 mb-2 block">Severity:</span>
            <div className="flex flex-wrap gap-2">
              {(['low', 'medium', 'high', 'critical'] as ErrorSeverity[]).map((severity) => (
                <button
                  key={severity}
                  onClick={() => toggleSeverity(severity)}
                  className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                    selectedSeverities.includes(severity)
                      ? 'bg-primary-100 border-primary-300 text-primary-800'
                      : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {severity}
                </button>
              ))}
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <span className="text-sm font-medium text-gray-700 mb-2 block">Status:</span>
            <div className="flex flex-wrap gap-2">
              {(['pending', 'fixing', 'fixed', 'failed', 'ignored'] as ErrorStatus[]).map((status) => (
                <button
                  key={status}
                  onClick={() => toggleStatus(status)}
                  className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                    selectedStatuses.includes(status)
                      ? 'bg-primary-100 border-primary-300 text-primary-800'
                      : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {status}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Active Filters */}
        {(selectedSeverities.length > 0 || selectedStatuses.length > 0 || searchTerm !== '') && (
          <div className="mt-4 flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Active filters:</span>
            {searchTerm && (
              <Badge variant="info">
                Search: "{searchTerm}"
                <button
                  onClick={() => setSearchTerm('')}
                  className="ml-2 hover:text-blue-900"
                >
                  ×
                </button>
              </Badge>
            )}
            <button
              onClick={() => {
                setSelectedSeverities([]);
                setSelectedStatuses([]);
                setSearchTerm('');
              }}
              className="text-sm text-primary-600 hover:text-primary-800 font-medium"
            >
              Clear all
            </button>
          </div>
        )}
      </Card>

      {/* Results Counter */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600">
          Showing <span className="font-semibold">{filteredErrors.length}</span> of{' '}
          <span className="font-semibold">{errors.length}</span> errors
        </p>
      </div>

      {/* Errors Table */}
      <Card padding="none">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Driver / Company
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Error Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Message
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Severity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Discovered
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <Loader2 className="w-8 h-8 animate-spin text-cyan-500 mx-auto" />
                    <p className="text-gray-500 mt-2">Loading errors...</p>
                  </td>
                </tr>
              ) : filteredErrors.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    <div className="flex flex-col items-center">
                      <Filter className="w-12 h-12 text-gray-400 mb-3" />
                      <p className="text-lg font-medium">No errors found</p>
                      <p className="text-sm mt-1">Try adjusting your filters or search term</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredErrors.map((error) => (
                  <tr key={error.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{error.driver_name}</div>
                        <div className="text-xs text-gray-500">{error.company_name}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{error.error_name}</div>
                      <div className="text-xs text-gray-500">{error.error_key}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-600 max-w-xs truncate" title={error.error_message}>
                        {error.error_message}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge className={getSeverityColor(error.severity)}>{error.severity}</Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge className={getStatusColor(error.status)}>{error.status}</Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{formatDate(error.discovered_at)}</div>
                      <div className="text-xs text-gray-500">{formatRelativeTime(error.discovered_at)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <Button variant="ghost" size="sm">
                        View
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
