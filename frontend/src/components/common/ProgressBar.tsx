import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle, XCircle, Clock, AlertCircle, Activity } from 'lucide-react';
import { Card } from './Card';

interface ProgressBarProps {
  scanId: string;
  onComplete?: (success: boolean) => void;
}

interface ProgressData {
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress_percent: number;
  current_driver: number;
  total_drivers: number;
  current_driver_id: string | null;
  message: string;
  current_step?: number;
  total_steps?: number;
  step?: string;
  step_message?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ scanId, onComplete }) => {
  const [progress, setProgress] = useState<ProgressData>({
    status: 'pending',
    progress_percent: 0,
    current_driver: 0,
    total_drivers: 0,
    current_driver_id: null,
    message: 'Инициализация...',
    current_step: 0,
    total_steps: 12,
    step: 'initializing',
    step_message: 'Инициализация...',
  });

  useEffect(() => {
    let intervalId: number | null = null;

    const fetchProgress = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/agent/scan/${scanId}/progress`);
        if (response.ok) {
          const data: ProgressData = await response.json();
          setProgress(data);

          // Stop polling when completed or failed
          if (data.status === 'completed' || data.status === 'failed') {
            if (intervalId) {
              clearInterval(intervalId);
            }
            if (onComplete) {
              onComplete(data.status === 'completed');
            }
          }
        }
      } catch (error) {
        console.error('Ошибка получения прогресса:', error);
      }
    };

    // Start polling
    fetchProgress();
    intervalId = window.setInterval(fetchProgress, 800); // Poll every 800ms for responsive updates

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [scanId, onComplete]);

  const getStatusIcon = () => {
    switch (progress.status) {
      case 'pending':
        return <Clock className="w-6 h-6 text-yellow-400 animate-pulse" />;
      case 'running':
        return <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-400" />;
      case 'failed':
        return <XCircle className="w-6 h-6 text-red-400" />;
    }
  };

  const getProgressBarColor = () => {
    switch (progress.status) {
      case 'pending':
        return 'bg-yellow-500';
      case 'running':
        return 'bg-gradient-to-r from-cyan-500 to-blue-500';
      case 'completed':
        return 'bg-gradient-to-r from-green-500 to-emerald-500';
      case 'failed':
        return 'bg-gradient-to-r from-red-500 to-rose-500';
    }
  };

  const getStatusText = () => {
    switch (progress.status) {
      case 'pending':
        return 'Ожидание запуска';
      case 'running':
        return 'Выполняется';
      case 'completed':
        return 'Успешно завершено';
      case 'failed':
        return 'Завершено с ошибкой';
    }
  };

  const getGlowColor = () => {
    switch (progress.status) {
      case 'pending':
        return 'shadow-neon-orange';
      case 'running':
        return 'shadow-neon-cyan';
      case 'completed':
        return 'shadow-neon-green';
      case 'failed':
        return 'shadow-neon-red';
    }
  };

  return (
    <Card variant="glass" className={`p-6 transition-all duration-300 ${getGlowColor()}`}>
      <div className="space-y-5">
        {/* Header with status icon and percentage */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4 flex-1">
            <div className="relative">
              {getStatusIcon()}
              {progress.status === 'running' && (
                <div className="absolute inset-0 animate-ping opacity-20">
                  <Activity className="w-6 h-6 text-cyan-400" />
                </div>
              )}
            </div>

            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-bold text-white leading-tight">
                {getStatusText()}
              </h3>
              <div className="flex items-center gap-3 mt-1.5">
                <p className="text-sm text-gray-400">
                  Водитель {progress.current_driver} / {progress.total_drivers}
                </p>
                {progress.current_step !== undefined && progress.total_steps && (
                  <>
                    <span className="text-gray-600">•</span>
                    <p className="text-sm text-gray-400">
                      Шаг {progress.current_step} / {progress.total_steps}
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="text-right">
            <div className="text-3xl font-bold text-white tabular-nums">
              {Math.round(progress.progress_percent)}%
            </div>
            <p className="text-xs text-gray-500 mt-1">завершено</p>
          </div>
        </div>

        {/* Main Progress Bar */}
        <div className="relative">
          <div className="relative h-3 bg-cyber-700/80 rounded-full overflow-hidden ring-1 ring-cyber-600">
            <div
              className={`absolute top-0 left-0 h-full ${getProgressBarColor()} transition-all duration-700 ease-out`}
              style={{ width: `${progress.progress_percent}%` }}
            >
              {/* Shimmer effect for running state */}
              {progress.status === 'running' && (
                <div
                  className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"
                  style={{ animationDuration: '1.5s' }}
                />
              )}

              {/* Pulse effect at the end of progress bar */}
              {progress.status === 'running' && progress.progress_percent > 0 && (
                <div className="absolute top-0 right-0 w-1 h-full bg-white/50 animate-pulse" />
              )}
            </div>
          </div>

          {/* Step markers (show 12 steps if available) */}
          {progress.total_steps && progress.total_steps > 1 && (
            <div className="absolute top-0 left-0 right-0 h-3 flex items-center">
              {Array.from({ length: progress.total_steps - 1 }).map((_, i) => {
                const markerPosition = ((i + 1) / (progress.total_steps || 1)) * 100;
                return (
                  <div
                    key={i}
                    className="absolute w-0.5 h-3 bg-cyber-900/50"
                    style={{ left: `${markerPosition}%` }}
                  />
                );
              })}
            </div>
          )}
        </div>

        {/* Current Action Message - Prominent */}
        <div className="bg-cyber-800/50 rounded-lg p-4 border border-cyan-500/20">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 mt-0.5">
              {progress.status === 'running' && (
                <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse shadow-neon-cyan" />
              )}
              {progress.status === 'completed' && (
                <div className="w-2 h-2 rounded-full bg-green-400" />
              )}
              {progress.status === 'failed' && (
                <AlertCircle className="w-4 h-4 text-red-400" />
              )}
              {progress.status === 'pending' && (
                <div className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-base font-medium text-white leading-relaxed">
                {progress.message}
              </p>

              {/* Detailed step message */}
              {progress.step_message && progress.step_message !== progress.message && (
                <p className="text-sm text-gray-400 mt-2 pl-3 border-l-2 border-cyan-500/50 italic">
                  {progress.step_message}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Current Driver ID - Subtle */}
        {progress.current_driver_id && progress.status === 'running' && (
          <div className="flex items-center gap-2 text-xs text-gray-500 font-mono">
            <div className="w-1.5 h-1.5 rounded-full bg-gray-600" />
            <span className="opacity-50">Driver ID:</span>
            <span className="text-gray-400">
              {progress.current_driver_id.substring(0, 8)}...{progress.current_driver_id.substring(progress.current_driver_id.length - 4)}
            </span>
          </div>
        )}

        {/* Success message */}
        {progress.status === 'completed' && (
          <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-3">
            <p className="text-sm text-green-300 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 flex-shrink-0" />
              <span>Сканирование успешно завершено! Результаты сохранены.</span>
            </p>
          </div>
        )}

        {/* Error message */}
        {progress.status === 'failed' && (
          <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3">
            <p className="text-sm text-red-300 flex items-center gap-2">
              <XCircle className="w-4 h-4 flex-shrink-0" />
              <span>Произошла ошибка. Проверьте логи для получения подробностей.</span>
            </p>
          </div>
        )}
      </div>
    </Card>
  );
};
