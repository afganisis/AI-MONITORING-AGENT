import React, { useState, useEffect } from 'react';
import { Search, Users, Building2, CheckCircle2, XCircle, Loader2, Play, Pause, StopCircle } from 'lucide-react';
import { Card, CardHeader } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { AIStatusIndicator } from '@/components/common/AIStatusIndicator';

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

const defaultConfig: AgentConfig = {
  state: 'stopped',
  polling_interval_seconds: 300,
  max_concurrent_fixes: 1,
  require_approval: false,
  dry_run_mode: false,
};

export const Control: React.FC = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(null);
  const [selectedDriverIds, setSelectedDriverIds] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);

  // Agent state
  const [agentConfig, setAgentConfig] = useState<AgentConfig>(defaultConfig);
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    fetchCompanies();
    fetchSelectedDrivers();
    fetchAgentConfig();

    const interval = setInterval(fetchAgentConfig, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchCompanies = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/companies');
      if (!response.ok) throw new Error('Failed to fetch companies');

      const data = await response.json();
      setCompanies(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error fetching companies:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSelectedDrivers = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/drivers/selected');
      if (response.ok) {
        const driverIds = await response.json();
        setSelectedDriverIds(new Set(driverIds));
      }
    } catch (err) {
      console.error('Error fetching selected drivers:', err);
    }
  };

  const fetchAgentConfig = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/agent/status');
      if (response.ok) {
        const data = await response.json();
        console.log('Agent config fetched:', data);
        setAgentConfig(data);
      }
    } catch (error) {
      console.error('Error fetching agent config:', error);
    }
  };

  const handleCompanyClick = (companyId: string) => {
    setSelectedCompanyId(selectedCompanyId === companyId ? null : companyId);
  };

  const handleDriverToggle = (driverId: string) => {
    const newSelected = new Set(selectedDriverIds);
    if (newSelected.has(driverId)) {
      newSelected.delete(driverId);
    } else {
      newSelected.add(driverId);
    }
    setSelectedDriverIds(newSelected);
  };

  const handleSelectAllDrivers = (company: Company) => {
    const newSelected = new Set(selectedDriverIds);
    const companyDriverIds = company.drivers.map(d => d.driver_id);
    const allSelected = companyDriverIds.every(id => newSelected.has(id));

    if (allSelected) {
      companyDriverIds.forEach(id => newSelected.delete(id));
    } else {
      companyDriverIds.forEach(id => newSelected.add(id));
    }
    setSelectedDriverIds(newSelected);
  };

  const handleSaveSelection = async () => {
    try {
      setSaving(true);
      const response = await fetch('http://localhost:8000/api/drivers/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ driver_ids: Array.from(selectedDriverIds) })
      });

      if (!response.ok) throw new Error('Failed to save selection');
      alert(`Выбрано ${selectedDriverIds.size} водителей для мониторинга!`);
    } catch (err) {
      alert('Ошибка: ' + (err instanceof Error ? err.message : 'Unknown error'));
    } finally {
      setSaving(false);
    }
  };

  const handleStartAgent = async () => {
    if (selectedDriverIds.size === 0) {
      alert('Выберите хотя бы одного водителя!');
      return;
    }

    if (!confirm('Запустить AI Agent? Он начнёт мониторинг и исправление ошибок.')) return;

    setIsUpdating(true);
    try {
      const response = await fetch('http://localhost:8000/api/agent/start', { method: 'POST' });
      if (response.ok) {
        await fetchAgentConfig();
        alert('AI Agent запущен!');
      }
    } catch (error) {
      console.error('Error starting agent:', error);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleStopAgent = async () => {
    if (!confirm('Остановить AI Agent?')) return;

    setIsUpdating(true);
    try {
      const response = await fetch('http://localhost:8000/api/agent/stop', { method: 'POST' });
      if (response.ok) {
        await fetchAgentConfig();
        alert('AI Agent остановлен!');
      }
    } catch (error) {
      console.error('Error stopping agent:', error);
    } finally {
      setIsUpdating(false);
    }
  };

  const handlePauseAgent = async () => {
    if (!confirm('Приостановить AI Agent?')) return;

    setIsUpdating(true);
    try {
      const response = await fetch('http://localhost:8000/api/agent/pause', { method: 'POST' });
      if (response.ok) {
        await fetchAgentConfig();
        alert('AI Agent приостановлен!');
      }
    } catch (error) {
      console.error('Error pausing agent:', error);
    } finally {
      setIsUpdating(false);
    }
  };

  const filteredCompanies = companies.filter(company =>
    company.company_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedCompany = companies.find(c => c.company_id === selectedCompanyId);

  const getStatusFromState = (state: string): 'running' | 'paused' | 'stopped' | 'processing' => {
    if (state === 'running') return 'running';
    if (state === 'paused') return 'paused';
    if (state === 'processing') return 'processing';
    return 'stopped';
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
      {/* Agent Status Banner */}
      <Card variant="hologram" glow="cyan">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <AIStatusIndicator status={getStatusFromState(agentConfig.state)} size="md" />
            <div>
              <h2 className="text-xl font-bold text-white">AI Agent</h2>
              <p className="text-sm text-gray-400 mt-1">
                {agentConfig.state === 'running' && `Опрос каждые ${agentConfig.polling_interval_seconds}s`}
                {agentConfig.state === 'paused' && 'Приостановлен'}
                {agentConfig.state === 'stopped' && 'Остановлен'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {agentConfig.state === 'stopped' && (
              <Button
                onClick={handleStartAgent}
                disabled={isUpdating || selectedDriverIds.size === 0}
                className="bg-green-600 hover:bg-green-700"
              >
                <Play className="w-4 h-4 mr-2" />
                Запустить
              </Button>
            )}

            {agentConfig.state === 'running' && (
              <>
                <Button
                  onClick={handlePauseAgent}
                  disabled={isUpdating}
                  variant="secondary"
                >
                  <Pause className="w-4 h-4 mr-2" />
                  Пауза
                </Button>
                <Button
                  onClick={handleStopAgent}
                  disabled={isUpdating}
                  className="bg-red-600 hover:bg-red-700"
                >
                  <StopCircle className="w-4 h-4 mr-2" />
                  Остановить
                </Button>
              </>
            )}

            {agentConfig.state === 'paused' && (
              <>
                <Button
                  onClick={handleStartAgent}
                  disabled={isUpdating}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Продолжить
                </Button>
                <Button
                  onClick={handleStopAgent}
                  disabled={isUpdating}
                  className="bg-red-600 hover:bg-red-700"
                >
                  <StopCircle className="w-4 h-4 mr-2" />
                  Остановить
                </Button>
              </>
            )}
          </div>
        </div>
      </Card>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Выбор водителей</h1>
          <p className="text-gray-400 text-sm mt-1">
            Выберите водителей для мониторинга AI Agent
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="info" className="text-base px-3 py-1.5">
            {selectedDriverIds.size} выбрано
          </Badge>

          <Button
            onClick={handleSaveSelection}
            disabled={selectedDriverIds.size === 0 || saving}
            className="bg-cyan-600 hover:bg-cyan-700"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Сохранение...
              </>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                Сохранить
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          placeholder="Поиск компаний..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 bg-cyber-800 border border-cyber-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
        />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Companies List */}
        <Card className="p-5">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center">
            <Building2 className="w-5 h-5 mr-2 text-cyan-400" />
            Компании ({filteredCompanies.length})
          </h2>

          <div className="space-y-2 max-h-[500px] overflow-y-auto">
            {filteredCompanies.map((company) => {
              const selectedCount = company.drivers.filter(d =>
                selectedDriverIds.has(d.driver_id)
              ).length;
              const isActive = company.company_id === selectedCompanyId;

              return (
                <div
                  key={company.company_id}
                  onClick={() => handleCompanyClick(company.company_id)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    isActive
                      ? 'bg-cyan-900/30 border-cyan-500'
                      : 'bg-cyber-700 border-cyber-600 hover:border-cyber-500'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-white text-sm">
                        {company.company_name}
                      </h3>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {company.drivers.length} водителей
                      </p>
                    </div>

                    {selectedCount > 0 && (
                      <Badge variant="success" className="text-xs">
                        {selectedCount}
                      </Badge>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Drivers List */}
        <Card className="p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-white flex items-center">
              <Users className="w-5 h-5 mr-2 text-cyan-400" />
              Водители
            </h2>

            {selectedCompany && (
              <Button
                onClick={() => handleSelectAllDrivers(selectedCompany)}
                variant="secondary"
                size="sm"
              >
                {selectedCompany.drivers.every(d => selectedDriverIds.has(d.driver_id))
                  ? 'Снять все'
                  : 'Выбрать все'}
              </Button>
            )}
          </div>

          {!selectedCompany ? (
            <div className="flex items-center justify-center h-64 text-gray-500">
              <p className="text-sm">Выберите компанию</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {selectedCompany.drivers.map((driver) => {
                const isSelected = selectedDriverIds.has(driver.driver_id);

                return (
                  <div
                    key={driver.driver_id}
                    onClick={() => handleDriverToggle(driver.driver_id)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-green-900/30 border-green-500'
                        : 'bg-cyber-700 border-cyber-600 hover:border-cyber-500'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {isSelected ? (
                        <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
                      ) : (
                        <XCircle className="w-5 h-5 text-gray-500 flex-shrink-0" />
                      )}

                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-white text-sm truncate">
                          {driver.driver_name}
                        </h3>
                        <p className="text-xs text-gray-400 mt-0.5 truncate">
                          {driver.driver_id.substring(0, 8)}...
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      </div>

      {/* Info */}
      {selectedDriverIds.size === 0 && (
        <Card className="p-4 bg-yellow-900/20 border-yellow-600">
          <p className="text-yellow-400 text-sm">
            Выберите водителей и сохраните выбор, затем запустите AI Agent
          </p>
        </Card>
      )}

      {selectedDriverIds.size > 0 && agentConfig.state === 'stopped' && (
        <Card className="p-4 bg-cyan-900/20 border-cyan-500">
          <p className="text-cyan-300 text-sm">
            <strong>{selectedDriverIds.size} водителей выбрано.</strong> Нажмите "Запустить" чтобы начать мониторинг
          </p>
        </Card>
      )}
    </div>
  );
};
