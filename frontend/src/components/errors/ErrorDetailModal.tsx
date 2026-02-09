import React from 'react';
import {
  X,
  AlertTriangle,
  CheckCircle,
  Wrench,
  FileText,
  Calendar,
  Tag,
  User,
  Building2,
} from 'lucide-react';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import {
  getErrorDescription,
  getCategoryInfo,
  formatErrorDateTime,
  getSeverityLabel,
  getStatusLabel,
} from '@/utils/errorDescriptions';

interface ErrorDetail {
  id: string;
  error_key: string;
  error_name: string;
  error_message: string;
  severity: string;
  status: string;
  category?: string;
  discovered_at: string;
  driver_name?: string;
  company_name?: string;
  location?: string;
  error_metadata?: Record<string, any>;
}

interface ErrorDetailModalProps {
  error: ErrorDetail | null;
  onClose: () => void;
}

export const ErrorDetailModal: React.FC<ErrorDetailModalProps> = ({ error, onClose }) => {
  if (!error) return null;

  const description = getErrorDescription(error.error_key);
  const category = getCategoryInfo(description.category);
  const dateTime = formatErrorDateTime(error.discovered_at);

  const getSeverityColor = (severity: string) => {
    const colors = {
      critical: 'bg-red-500/20 text-red-400 border-red-500/50',
      high: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
      medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
      low: 'bg-gray-500/20 text-gray-400 border-gray-500/50',
    };
    return colors[severity as keyof typeof colors] || colors.low;
  };

  const getStatusColor = (status: string) => {
    const colors = {
      pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
      fixing: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50',
      fixed: 'bg-green-500/20 text-green-400 border-green-500/50',
      failed: 'bg-red-500/20 text-red-400 border-red-500/50',
    };
    return colors[status as keyof typeof colors] || 'bg-gray-500/20 text-gray-400';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-cyber-800 border border-cyber-600 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-cyber-600">
          <div className="flex items-start gap-4">
            <div className={`p-3 rounded-xl ${getSeverityColor(error.severity)}`}>
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white mb-1">
                {description.name}
              </h2>
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant={error.severity as any} className="text-xs">
                  {getSeverityLabel(error.severity)}
                </Badge>
                <span className={`px-2 py-0.5 rounded text-xs border ${getStatusColor(error.status)}`}>
                  {getStatusLabel(error.status)}
                </span>
                <span className="text-xs text-gray-500 font-mono">
                  #{error.id.slice(0, 8)}
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white hover:bg-cyber-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 overflow-y-auto max-h-[60vh]">
          {/* Description */}
          <div className="bg-cyber-700/50 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <FileText className="w-4 h-4 text-cyan-400" />
              <h3 className="font-semibold text-white">Описание</h3>
            </div>
            <p className="text-gray-300 leading-relaxed">
              {description.description}
            </p>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-2 gap-4">
            {/* Date/Time */}
            <div className="bg-cyber-700/50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="w-4 h-4 text-purple-400" />
                <span className="text-sm text-gray-400">Дата и время</span>
              </div>
              <div className="text-white font-semibold">{dateTime.date}</div>
              <div className="text-cyan-400 font-mono">{dateTime.time}</div>
              <div className="text-xs text-gray-500 mt-1">{dateTime.relative}</div>
            </div>

            {/* Category */}
            <div className="bg-cyber-700/50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Tag className="w-4 h-4 text-green-400" />
                <span className="text-sm text-gray-400">Категория</span>
              </div>
              <div className="text-white font-semibold">{category.name}</div>
              <div className="text-xs text-gray-500 mt-1">{category.description}</div>
            </div>

            {/* Driver */}
            {error.driver_name && (
              <div className="bg-cyber-700/50 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <User className="w-4 h-4 text-blue-400" />
                  <span className="text-sm text-gray-400">Водитель</span>
                </div>
                <div className="text-white font-semibold">{error.driver_name}</div>
              </div>
            )}

            {/* Company */}
            {error.company_name && (
              <div className="bg-cyber-700/50 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Building2 className="w-4 h-4 text-orange-400" />
                  <span className="text-sm text-gray-400">Компания</span>
                </div>
                <div className="text-white font-semibold">{error.company_name}</div>
              </div>
            )}
          </div>

          {/* Error Key */}
          <div className="bg-cyber-700/50 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm text-gray-400">Код ошибки (Error Key)</span>
            </div>
            <code className="text-cyan-400 font-mono bg-cyber-900 px-3 py-1 rounded">
              {error.error_key}
            </code>
          </div>

          {/* Original Message */}
          {error.error_message && (
            <div className="bg-cyber-700/50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm text-gray-400">Сообщение системы</span>
              </div>
              <p className="text-gray-300 text-sm font-mono bg-cyber-900 p-3 rounded">
                {error.error_message}
              </p>
            </div>
          )}

          {/* How to Fix */}
          <div className="bg-green-900/20 border border-green-500/30 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Wrench className="w-4 h-4 text-green-400" />
              <h3 className="font-semibold text-green-400">Как исправить</h3>
            </div>
            <p className="text-gray-300 leading-relaxed">
              {description.howToFix}
            </p>
          </div>

          {/* Metadata */}
          {error.error_metadata && Object.keys(error.error_metadata).length > 0 && (
            <div className="bg-cyber-700/50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-sm text-gray-400">Дополнительные данные</span>
              </div>
              <pre className="text-xs text-gray-300 font-mono bg-cyber-900 p-3 rounded overflow-x-auto">
                {JSON.stringify(error.error_metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-cyber-600 bg-cyber-900/50">
          <Button variant="secondary" onClick={onClose}>
            Закрыть
          </Button>
          {error.status === 'pending' && (
            <Button className="bg-green-600 hover:bg-green-700">
              <CheckCircle className="w-4 h-4 mr-2" />
              Отметить как решенное
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
