import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

// ============================================================================
// TYPES
// ============================================================================

interface Driver {
  driver_id: string;
  driver_name: string;
}

interface Company {
  company_id: string;
  company_name: string;
  drivers: Driver[];
}

interface AgentConfig {
  state: string;
  polling_interval_seconds: number;
  max_concurrent_fixes: number;
  require_approval: boolean;
  dry_run_mode: boolean;
}

interface ErrorStats {
  total_errors: number;
  errors_pending: number;
  errors_fixing: number;
  errors_fixed: number;
  errors_failed: number;
  fixes_today: number;
  success_rate: number;
  errors_by_severity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

interface Error {
  id: string;
  error_key: string;
  error_name?: string;
  severity: string;
  status: string;
  category?: string;
  fix_strategy?: string;
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
  recent_errors: RecentError[];
}

interface CacheTimestamps {
  companies: number | null;
  agentConfig: number | null;
  errorStats: number | null;
  recentErrors: number | null;
  recentFixes: number | null;
  errorsByDriver: number | null;
}

// Scan Activity types
interface ScanActivity {
  id: string;
  type: 'smart_analyze' | 'full_scan' | 'log_scan';
  status: 'running' | 'completed' | 'failed';
  companyId?: string;
  companyName?: string;
  driverIds: string[];
  driverCount: number;
  startedAt: string;
  completedAt?: string;
  username?: string;
  message?: string;
}

// ============================================================================
// CONTEXT TYPE
// ============================================================================

interface DataContextType {
  // Companies data (for Control page)
  companies: Company[];
  companiesLoading: boolean;
  refreshCompanies: () => Promise<void>;

  // Agent config (for Control page)
  agentConfig: AgentConfig;
  agentConfigLoading: boolean;
  refreshAgentConfig: () => Promise<void>;

  // Error stats (for Activity page)
  errorStats: ErrorStats;
  errorStatsLoading: boolean;
  refreshErrorStats: () => Promise<void>;

  // Recent errors (for Activity page)
  recentErrors: Error[];
  recentErrorsLoading: boolean;
  refreshRecentErrors: () => Promise<void>;

  // Recent fixes (for Activity page)
  recentFixes: Fix[];
  recentFixesLoading: boolean;
  refreshRecentFixes: () => Promise<void>;

  // Errors by driver (for Results page)
  errorsByDriver: ErrorByDriver[];
  errorsByDriverLoading: boolean;
  refreshErrorsByDriver: () => Promise<void>;

  // Scan activity (for Activity page)
  scanActivities: ScanActivity[];
  addScanActivity: (activity: Omit<ScanActivity, 'id' | 'startedAt'>) => string;
  updateScanActivity: (id: string, updates: Partial<ScanActivity>) => void;

  // Refresh all data
  refreshAll: () => Promise<void>;

  // Cache info
  getCacheAge: (key: keyof CacheTimestamps) => number | null;
  isCacheStale: (key: keyof CacheTimestamps, maxAgeMs?: number) => boolean;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

// ============================================================================
// HOOK
// ============================================================================

export const useData = () => {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
};

// ============================================================================
// DEFAULT VALUES
// ============================================================================

const defaultAgentConfig: AgentConfig = {
  state: 'stopped',
  polling_interval_seconds: 300,
  max_concurrent_fixes: 1,
  require_approval: false,
  dry_run_mode: false,
};

const defaultErrorStats: ErrorStats = {
  total_errors: 0,
  errors_pending: 0,
  errors_fixing: 0,
  errors_fixed: 0,
  errors_failed: 0,
  fixes_today: 0,
  success_rate: 0,
  errors_by_severity: { critical: 0, high: 0, medium: 0, low: 0 },
};

// ============================================================================
// PROVIDER
// ============================================================================

interface DataProviderProps {
  children: ReactNode;
}

const API_BASE = 'http://localhost:8000/api';
const CACHE_DURATION = 30000; // 30 seconds

export const DataProvider: React.FC<DataProviderProps> = ({ children }) => {
  // Companies
  const [companies, setCompanies] = useState<Company[]>([]);
  const [companiesLoading, setCompaniesLoading] = useState(false);

  // Agent config
  const [agentConfig, setAgentConfig] = useState<AgentConfig>(defaultAgentConfig);
  const [agentConfigLoading, setAgentConfigLoading] = useState(false);

  // Error stats
  const [errorStats, setErrorStats] = useState<ErrorStats>(defaultErrorStats);
  const [errorStatsLoading, setErrorStatsLoading] = useState(false);

  // Recent errors
  const [recentErrors, setRecentErrors] = useState<Error[]>([]);
  const [recentErrorsLoading, setRecentErrorsLoading] = useState(false);

  // Recent fixes
  const [recentFixes, setRecentFixes] = useState<Fix[]>([]);
  const [recentFixesLoading, setRecentFixesLoading] = useState(false);

  // Errors by driver
  const [errorsByDriver, setErrorsByDriver] = useState<ErrorByDriver[]>([]);
  const [errorsByDriverLoading, setErrorsByDriverLoading] = useState(false);

  // Scan activities (kept in memory, persisted to localStorage)
  const [scanActivities, setScanActivities] = useState<ScanActivity[]>(() => {
    try {
      const saved = localStorage.getItem('scanActivities');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Persist scan activities to localStorage
  useEffect(() => {
    try {
      // Keep only last 50 activities
      const toSave = scanActivities.slice(0, 50);
      localStorage.setItem('scanActivities', JSON.stringify(toSave));
    } catch {
      // Ignore storage errors
    }
  }, [scanActivities]);

  const addScanActivity = useCallback((activity: Omit<ScanActivity, 'id' | 'startedAt'>): string => {
    const id = `scan_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const newActivity: ScanActivity = {
      ...activity,
      id,
      startedAt: new Date().toISOString(),
    };
    setScanActivities(prev => [newActivity, ...prev]);
    return id;
  }, []);

  const updateScanActivity = useCallback((id: string, updates: Partial<ScanActivity>) => {
    setScanActivities(prev => prev.map(activity =>
      activity.id === id ? { ...activity, ...updates } : activity
    ));
  }, []);

  // Cache timestamps
  const [cacheTimestamps, setCacheTimestamps] = useState<CacheTimestamps>({
    companies: null,
    agentConfig: null,
    errorStats: null,
    recentErrors: null,
    recentFixes: null,
    errorsByDriver: null,
  });

  // ============================================================================
  // CACHE HELPERS
  // ============================================================================

  const updateCacheTimestamp = (key: keyof CacheTimestamps) => {
    setCacheTimestamps(prev => ({ ...prev, [key]: Date.now() }));
  };

  const getCacheAge = (key: keyof CacheTimestamps): number | null => {
    const timestamp = cacheTimestamps[key];
    if (timestamp === null) return null;
    return Date.now() - timestamp;
  };

  const isCacheStale = (key: keyof CacheTimestamps, maxAgeMs: number = CACHE_DURATION): boolean => {
    const age = getCacheAge(key);
    if (age === null) return true;
    return age > maxAgeMs;
  };

  // ============================================================================
  // FETCH FUNCTIONS
  // ============================================================================

  const refreshCompanies = useCallback(async (force: boolean = false) => {
    // Skip if cache is fresh and not forced
    if (!force && !isCacheStale('companies')) {
      return;
    }

    setCompaniesLoading(true);
    try {
      const response = await fetch(`${API_BASE}/companies`);
      if (!response.ok) throw new Error('Failed to fetch companies');
      const data = await response.json();
      setCompanies(data);
      updateCacheTimestamp('companies');
    } catch (error) {
      console.error('Error fetching companies:', error);
    } finally {
      setCompaniesLoading(false);
    }
  }, [cacheTimestamps]);

  const refreshAgentConfig = useCallback(async (force: boolean = false) => {
    // Skip if cache is fresh and not forced
    if (!force && !isCacheStale('agentConfig', 5000)) {
      // Agent config has 5s cache (more frequent updates needed)
      return;
    }

    setAgentConfigLoading(true);
    try {
      const response = await fetch(`${API_BASE}/agent/status`);
      if (response.ok) {
        const data = await response.json();
        setAgentConfig(data);
        updateCacheTimestamp('agentConfig');
      }
    } catch (error) {
      console.error('Error fetching agent config:', error);
    } finally {
      setAgentConfigLoading(false);
    }
  }, [cacheTimestamps]);

  const refreshErrorStats = useCallback(async (force: boolean = false) => {
    // Skip if cache is fresh and not forced
    if (!force && !isCacheStale('errorStats')) {
      return;
    }

    setErrorStatsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/errors/stats`);
      if (response.ok) {
        const statsData = await response.json();

        // Transform stats to match expected format
        const transformedStats: ErrorStats = {
          total_errors: statsData.total_errors || 0,
          errors_pending: statsData.by_status?.pending || 0,
          errors_fixing: statsData.by_status?.fixing || 0,
          errors_fixed: statsData.by_status?.fixed || 0,
          errors_failed: statsData.by_status?.failed || 0,
          fixes_today: 0,
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
        setErrorStats(transformedStats);
        updateCacheTimestamp('errorStats');
      }
    } catch (error) {
      console.error('Error fetching error stats:', error);
    } finally {
      setErrorStatsLoading(false);
    }
  }, [cacheTimestamps]);

  const refreshRecentErrors = useCallback(async (force: boolean = false) => {
    // Skip if cache is fresh and not forced
    if (!force && !isCacheStale('recentErrors')) {
      return;
    }

    setRecentErrorsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/errors?page=1&page_size=10`);
      if (response.ok) {
        const data = await response.json();
        setRecentErrors(data.errors || []);
        updateCacheTimestamp('recentErrors');
      }
    } catch (error) {
      console.error('Error fetching recent errors:', error);
    } finally {
      setRecentErrorsLoading(false);
    }
  }, [cacheTimestamps]);

  const refreshRecentFixes = useCallback(async (force: boolean = false) => {
    // Skip if cache is fresh and not forced
    if (!force && !isCacheStale('recentFixes')) {
      return;
    }

    setRecentFixesLoading(true);
    try {
      const response = await fetch(`${API_BASE}/fixes?page=1&page_size=10`);
      if (response.ok) {
        const data = await response.json();
        setRecentFixes(data.fixes || []);
        updateCacheTimestamp('recentFixes');
      }
    } catch (error) {
      console.error('Error fetching recent fixes:', error);
    } finally {
      setRecentFixesLoading(false);
    }
  }, [cacheTimestamps]);

  const refreshErrorsByDriver = useCallback(async (force: boolean = false) => {
    // Skip if cache is fresh and not forced
    if (!force && !isCacheStale('errorsByDriver')) {
      return;
    }

    setErrorsByDriverLoading(true);
    try {
      const response = await fetch(`${API_BASE}/errors/by-driver`);
      if (response.ok) {
        const data = await response.json();
        setErrorsByDriver(data.results || []);
        updateCacheTimestamp('errorsByDriver');
      }
    } catch (error) {
      console.error('Error fetching errors by driver:', error);
    } finally {
      setErrorsByDriverLoading(false);
    }
  }, [cacheTimestamps]);

  const refreshAll = useCallback(async () => {
    await Promise.all([
      refreshCompanies(true),
      refreshAgentConfig(true),
      refreshErrorStats(true),
      refreshRecentErrors(true),
      refreshRecentFixes(true),
      refreshErrorsByDriver(true),
    ]);
  }, [
    refreshCompanies,
    refreshAgentConfig,
    refreshErrorStats,
    refreshRecentErrors,
    refreshRecentFixes,
    refreshErrorsByDriver,
  ]);

  // ============================================================================
  // BACKGROUND POLLING
  // ============================================================================

  useEffect(() => {
    // Initial fetch
    refreshAll();

    // Background polling with different intervals
    const agentConfigInterval = setInterval(() => refreshAgentConfig(), 5000);
    const activityInterval = setInterval(() => {
      refreshErrorStats();
      refreshRecentErrors();
      refreshRecentFixes();
    }, 10000);
    const resultsInterval = setInterval(() => refreshErrorsByDriver(), 15000);
    const companiesInterval = setInterval(() => refreshCompanies(), 60000); // Less frequent

    return () => {
      clearInterval(agentConfigInterval);
      clearInterval(activityInterval);
      clearInterval(resultsInterval);
      clearInterval(companiesInterval);
    };
  }, []);

  // ============================================================================
  // CONTEXT VALUE
  // ============================================================================

  const value: DataContextType = {
    companies,
    companiesLoading,
    refreshCompanies: () => refreshCompanies(true),

    agentConfig,
    agentConfigLoading,
    refreshAgentConfig: () => refreshAgentConfig(true),

    errorStats,
    errorStatsLoading,
    refreshErrorStats: () => refreshErrorStats(true),

    recentErrors,
    recentErrorsLoading,
    refreshRecentErrors: () => refreshRecentErrors(true),

    recentFixes,
    recentFixesLoading,
    refreshRecentFixes: () => refreshRecentFixes(true),

    errorsByDriver,
    errorsByDriverLoading,
    refreshErrorsByDriver: () => refreshErrorsByDriver(true),

    scanActivities,
    addScanActivity,
    updateScanActivity,

    refreshAll,
    getCacheAge,
    isCacheStale,
  };

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
};
