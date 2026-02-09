import React, { useState } from 'react';
import { Search, Users, Building2, XCircle, Loader2, Play, Pause, StopCircle, FileSearch, Microscope, CheckCircle2 } from 'lucide-react';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { AIStatusIndicator } from '@/components/common/AIStatusIndicator';
import { ProgressBar } from '@/components/common/ProgressBar';
import { useData } from '@/contexts/DataContext';

interface Driver {
  driver_id: string;
  driver_name: string;
}

interface Company {
  company_id: string;
  company_name: string;
  drivers: Driver[];
}

export const Control: React.FC = () => {
  // Use global data context
  const {
    companies,
    companiesLoading,
    agentConfig,
    refreshAgentConfig,
    refreshErrorsByDriver,
    refreshErrorStats,
    refreshRecentErrors,
    addScanActivity,
    updateScanActivity,
  } = useData();

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(null);
  const [selectedDriverIds, setSelectedDriverIds] = useState<Set<string>>(new Set());
  const [scanning, setScanning] = useState(false);
  const [currentScanId, setCurrentScanId] = useState<string | null>(null);
  const [currentActivityId, setCurrentActivityId] = useState<string | null>(null);
  const [scanWithLogs, setScanWithLogs] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

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

  const handleSmartAnalyze = async (withLogs: boolean = false) => {
    if (selectedDriverIds.size === 0 && !selectedCompanyId) {
      alert('Выберите компанию или водителей для сканирования!');
      return;
    }

    const driverCount = selectedDriverIds.size || 'всех';
    const scanType = withLogs ? 'Smart Analyze + Сканирование логов' : 'Smart Analyze';
    const message = selectedCompanyId
      ? `Запустить ${scanType} для компании?`
      : `Запустить ${scanType} для ${driverCount} водителей?`;

    if (!confirm(message)) return;

    // Get company name for activity tracking
    const selectedCompany = companies.find(c => c.company_id === selectedCompanyId);
    const companyName = selectedCompany?.company_name;

    try {
      setScanning(true);
      setScanWithLogs(withLogs);
      const response = await fetch('http://localhost:8000/api/agent/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: selectedCompanyId,
          driver_ids: Array.from(selectedDriverIds),
          scan_all: false,
          scan_logs: withLogs
        })
      });

      if (!response.ok) throw new Error('Failed to start scan');

      const data = await response.json();
      setCurrentScanId(data.scan_id);

      // Track activity
      const activityId = addScanActivity({
        type: withLogs ? 'full_scan' : 'smart_analyze',
        status: 'running',
        companyId: selectedCompanyId || undefined,
        companyName: companyName,
        driverIds: Array.from(selectedDriverIds),
        driverCount: data.driver_count || selectedDriverIds.size,
      });
      setCurrentActivityId(activityId);

      console.log(`Сканирование запущено: ${data.scan_id}`);
    } catch (err) {
      alert('Ошибка: ' + (err instanceof Error ? err.message : 'Unknown error'));
      setScanning(false);
      setCurrentScanId(null);
    }
  };

  const handleLogScanOnly = async () => {
    if (selectedDriverIds.size === 0 && !selectedCompanyId) {
      alert('Выберите компанию или водителей для сканирования!');
      return;
    }

    const driverCount = selectedDriverIds.size || 'всех';
    const message = selectedCompanyId
      ? `Запустить сканирование логов для компании?`
      : `Запустить сканирование логов для ${driverCount} водителей?`;

    if (!confirm(message)) return;

    // Get company name for activity tracking
    const selectedCompany = companies.find(c => c.company_id === selectedCompanyId);
    const companyName = selectedCompany?.company_name;

    try {
      setScanning(true);
      setScanWithLogs(true);

      // Создаем специальный endpoint для сканирования только логов
      const response = await fetch('http://localhost:8000/api/agent/scan-logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: selectedCompanyId,
          driver_ids: Array.from(selectedDriverIds),
        })
      });

      if (!response.ok) throw new Error('Failed to start log scan');

      const data = await response.json();
      setCurrentScanId(data.scan_id);

      // Track activity
      const activityId = addScanActivity({
        type: 'log_scan',
        status: 'running',
        companyId: selectedCompanyId || undefined,
        companyName: companyName,
        driverIds: Array.from(selectedDriverIds),
        driverCount: data.driver_count || selectedDriverIds.size,
      });
      setCurrentActivityId(activityId);

      console.log(`Сканирование логов запущено: ${data.scan_id}`);
    } catch (err) {
      alert('Ошибка: ' + (err instanceof Error ? err.message : 'Unknown error'));
      setScanning(false);
      setCurrentScanId(null);
    }
  };

  const handleScanComplete = async (success: boolean) => {
    setScanning(false);
    setCurrentScanId(null);

    // Update activity status
    if (currentActivityId) {
      updateScanActivity(currentActivityId, {
        status: success ? 'completed' : 'failed',
        completedAt: new Date().toISOString(),
        message: success ? 'Сканирование завершено успешно' : 'Сканирование завершено с ошибками',
      });
      setCurrentActivityId(null);
    }

    // Refresh data in all related pages
    await Promise.all([
      refreshErrorsByDriver(),
      refreshErrorStats(),
      refreshRecentErrors(),
    ]);

    if (success) {
      alert('✅ Сканирование успешно завершено!\n\nДанные обновлены. Проверьте вкладку Results для просмотра результатов.');
    } else {
      alert('❌ Сканирование завершено с ошибками.\n\nПроверьте логи для деталей.');
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
        await refreshAgentConfig();
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
        await refreshAgentConfig();
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
        await refreshAgentConfig();
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

  if (companiesLoading && companies.length === 0) {
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
            onClick={() => handleSmartAnalyze(false)}
            disabled={scanning || (selectedDriverIds.size === 0 && !selectedCompanyId)}
            className="bg-purple-600 hover:bg-purple-700"
            glow={scanning && !scanWithLogs}
          >
            {scanning && !scanWithLogs ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Анализ...
              </>
            ) : (
              <>
                <Microscope className="w-4 h-4 mr-2" />
                Smart Analyze
              </>
            )}
          </Button>

          <Button
            onClick={() => handleSmartAnalyze(true)}
            disabled={scanning || (selectedDriverIds.size === 0 && !selectedCompanyId)}
            className="bg-orange-600 hover:bg-orange-700"
            glow={scanning && scanWithLogs}
          >
            {scanning && scanWithLogs ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Полное сканирование...
              </>
            ) : (
              <>
                <FileSearch className="w-4 h-4 mr-2" />
                Полное сканирование
              </>
            )}
          </Button>

          <Button
            onClick={() => handleLogScanOnly()}
            disabled={scanning || (selectedDriverIds.size === 0 && !selectedCompanyId)}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {scanning && scanWithLogs ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Сканирую логи...
              </>
            ) : (
              <>
                <FileSearch className="w-4 h-4 mr-2" />
                Только логи
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

      {/* Progress Bar */}
      {currentScanId && scanning && (
        <ProgressBar scanId={currentScanId} onComplete={handleScanComplete} />
      )}

      {/* Info */}
      {!scanning && selectedDriverIds.size === 0 && (
        <Card className="p-4 bg-yellow-900/20 border-yellow-600">
          <p className="text-yellow-400 text-sm">
            Выберите водителей, затем запустите сканирование или AI Agent
          </p>
        </Card>
      )}

      {!scanning && selectedDriverIds.size > 0 && agentConfig.state === 'stopped' && (
        <Card className="p-4 bg-cyan-900/20 border-cyan-500">
          <p className="text-cyan-300 text-sm">
            <strong>{selectedDriverIds.size} водителей выбрано.</strong> Запустите сканирование или нажмите "Запустить" для автоматического мониторинга.
          </p>
        </Card>
      )}

      {/* Instructions */}
      {!scanning && (
        <Card className="p-5 bg-cyber-800/50 border-cyber-600">
          <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
            <FileSearch className="w-5 h-5 text-cyan-400" />
            Типы сканирования
          </h3>
          <div className="space-y-3 text-sm text-gray-300">
            <div className="flex items-start gap-3">
              <Microscope className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-purple-400">Smart Analyze</strong>
                <p className="text-gray-400 mt-1">Быстрый анализ через Fortex API (~5-10 сек). Находит ошибки в логах драйверов за последние 7 дней. Результаты сохраняются в БД.</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <FileSearch className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-orange-400">Полное сканирование</strong>
                <p className="text-gray-400 mt-1">Smart Analyze + детальное сканирование логов через Playwright (~2-5 мин на драйвера). Открывает UI Fortex, заходит в логи, извлекает полные данные за 9 дней и сохраняет локально в JSON файлы.</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <FileSearch className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-blue-400">Только логи</strong>
                <p className="text-gray-400 mt-1">Сканирование только логов через Playwright (~2-5 мин на драйвера). Открывает UI Fortex, заходит в логи каждого драйвера и сохраняет данные локально в JSON файлы. БЕЗ анализа ошибок.</p>
              </div>
            </div>
            <div className="pt-2 border-t border-cyber-600 flex items-start gap-2">
              <span className="text-yellow-400 text-base">💡</span>
              <div>
                <span className="text-yellow-400 font-semibold">Совет:</span>
                <span className="text-gray-400 ml-2">Используйте "Smart Analyze" для быстрой проверки ошибок, "Только логи" для просмотра и сохранения данных логов, "Полное сканирование" для комплексного анализа.</span>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
