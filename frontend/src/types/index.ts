// Error types from zeroVios.js ERROR_FILTERS
export type ErrorKey =
  | 'sequentialIdBreak'
  | 'odometerError'
  | 'engineHoursAfterShutdown'
  | 'noDataInOdometerOrEngineHours'
  | 'locationError'
  | 'locationChangedError'
  | 'locationDidNotChangeWarning'
  | 'drivingOriginWarning'
  | 'incorrectStatusPlacementError'
  | 'twoIdenticalStatusesError'
  | 'missingIntermediateError'
  | 'incorrectIntermediatePlacementError'
  | 'diagnosticEvent'
  | 'noPowerUpError'
  | 'noShutdownError'
  | 'speedHigherThanLimit'
  | 'speedMuchHigherThanLimit'
  | 'unidentifiedDriverEvent'
  | 'eventIsNotDownloaded'
  | 'eventHasManualLocation'
  | 'excessiveLogInWarning'
  | 'excessiveLogOutWarning';

export type ErrorCategory =
  | 'data_integrity'
  | 'location_movement'
  | 'status_event'
  | 'diagnostic'
  | 'speed'
  | 'authentication'
  | 'uncategorized';

export type FixStrategy = 'obsolete' | 'info_only' | 'ai_repair' | 'custom';

export type ErrorSeverity = 'low' | 'medium' | 'high' | 'critical';

export type ErrorStatus = 'pending' | 'fixing' | 'fixed' | 'failed' | 'ignored';

export interface ErrorRecord {
  id: string;
  zeroeld_log_id?: string;
  zeroeld_event_id?: string;
  driver_id: string;
  driver_name?: string;
  company_id: string;
  company_name?: string;
  error_key: ErrorKey;
  error_name: string;
  error_message: string;
  severity: ErrorSeverity;
  status: ErrorStatus;
  metadata?: Record<string, any>;
  discovered_at: string;
  fixed_at?: string;
  created_at: string;
}

export type FixStatus =
  | 'pending_approval'
  | 'approved'
  | 'executing'
  | 'success'
  | 'failed'
  | 'rejected';

export interface Fix {
  id: string;
  error_id: string;
  strategy_name: string;
  fix_description: string;
  api_calls?: any[];
  status: FixStatus;
  result_message?: string;
  requires_approval: boolean;
  approved_by?: string;
  approved_at?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export type AgentState = 'stopped' | 'starting' | 'running' | 'paused' | 'stopping';

export interface AgentConfig {
  id: number;
  state: AgentState;
  polling_interval_seconds: number;
  max_concurrent_fixes: number;
  require_approval: boolean;
  dry_run_mode: boolean;
  created_at: string;
  updated_at: string;
}

export interface AgentStats {
  total_errors: number;
  errors_pending: number;
  errors_fixing: number;
  errors_fixed: number;
  errors_failed: number;
  fixes_today: number;
  success_rate: number;
  errors_by_type: Record<ErrorKey, number>;
  errors_by_severity: Record<ErrorSeverity, number>;
}

export interface AuditLog {
  id: string;
  action_type: string;
  entity_type?: string;
  entity_id?: string;
  user_id?: string;
  details?: Record<string, any>;
  ip_address?: string;
  created_at: string;
}

export interface ErrorFilters {
  status?: ErrorStatus[];
  severity?: ErrorSeverity[];
  error_key?: ErrorKey[];
  company_id?: string;
  driver_id?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface PaginationParams {
  page: number;
  limit: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

// WebSocket message types
export type WSMessageType =
  | 'error_discovered'
  | 'fix_proposed'
  | 'fix_approved'
  | 'fix_rejected'
  | 'fix_started'
  | 'fix_success'
  | 'fix_failed'
  | 'agent_status_changed';

export interface WSMessage {
  type: WSMessageType;
  data: any;
  timestamp: string;
}
