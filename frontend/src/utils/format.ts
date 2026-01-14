import { format, formatDistanceToNow } from 'date-fns';
import { ErrorSeverity, ErrorStatus, FixStatus, AgentState } from '@/types';

export const formatDate = (date: string | Date): string => {
  return format(new Date(date), 'MMM dd, yyyy HH:mm');
};

export const formatRelativeTime = (date: string | Date): string => {
  return formatDistanceToNow(new Date(date), { addSuffix: true });
};

export const getSeverityColor = (severity: ErrorSeverity): string => {
  const colors: Record<ErrorSeverity, string> = {
    low: 'bg-gray-100 text-gray-800 border-gray-200',
    medium: 'bg-blue-100 text-blue-800 border-blue-200',
    high: 'bg-warning-100 text-warning-800 border-warning-200',
    critical: 'bg-danger-100 text-danger-800 border-danger-200',
  };
  return colors[severity];
};

export const getStatusColor = (status: ErrorStatus): string => {
  const colors: Record<ErrorStatus, string> = {
    pending: 'bg-gray-100 text-gray-800 border-gray-200',
    fixing: 'bg-blue-100 text-blue-800 border-blue-200',
    fixed: 'bg-success-100 text-success-800 border-success-200',
    failed: 'bg-danger-100 text-danger-800 border-danger-200',
    ignored: 'bg-gray-100 text-gray-600 border-gray-200',
  };
  return colors[status];
};

export const getFixStatusColor = (status: FixStatus): string => {
  const colors: Record<FixStatus, string> = {
    pending_approval: 'bg-warning-100 text-warning-800 border-warning-200',
    approved: 'bg-success-100 text-success-800 border-success-200',
    executing: 'bg-blue-100 text-blue-800 border-blue-200',
    success: 'bg-success-100 text-success-800 border-success-200',
    failed: 'bg-danger-100 text-danger-800 border-danger-200',
    rejected: 'bg-gray-100 text-gray-800 border-gray-200',
  };
  return colors[status];
};

export const getAgentStateColor = (state: AgentState): string => {
  const colors: Record<AgentState, string> = {
    stopped: 'bg-gray-100 text-gray-800',
    starting: 'bg-blue-100 text-blue-800',
    running: 'bg-success-100 text-success-800',
    paused: 'bg-warning-100 text-warning-800',
    stopping: 'bg-warning-100 text-warning-800',
  };
  return colors[state];
};

export const formatErrorKey = (key: string): string => {
  return key
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, (str) => str.toUpperCase())
    .trim();
};

export const formatPercentage = (value: number): string => {
  return `${Math.round(value)}%`;
};

export const formatNumber = (value: number): string => {
  return new Intl.NumberFormat('en-US').format(value);
};
