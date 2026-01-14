import React, { useState } from 'react';
import { Card, CardHeader } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { Play, Pause, StopCircle, Settings, AlertTriangle } from 'lucide-react';
import { mockAgentConfig } from '@/data/mockData';
import { AgentState } from '@/types';
import { getAgentStateColor } from '@/utils/format';

export const AgentControl: React.FC = () => {
  const [config, setConfig] = useState(mockAgentConfig);
  const [isUpdating, setIsUpdating] = useState(false);

  const handleStart = async () => {
    if (confirm('Start the AI Agent? It will begin monitoring and proposing fixes.')) {
      setIsUpdating(true);
      // API call would go here
      setTimeout(() => {
        setConfig({ ...config, state: 'running' });
        setIsUpdating(false);
      }, 1000);
    }
  };

  const handleStop = async () => {
    if (confirm('Stop the AI Agent? Active operations will be completed first.')) {
      setIsUpdating(true);
      setTimeout(() => {
        setConfig({ ...config, state: 'stopped' });
        setIsUpdating(false);
      }, 1000);
    }
  };

  const handlePause = async () => {
    if (confirm('Pause the AI Agent? Monitoring continues but no fixes will be proposed.')) {
      setIsUpdating(true);
      setTimeout(() => {
        setConfig({ ...config, state: 'paused' });
        setIsUpdating(false);
      }, 1000);
    }
  };

  const toggleDryRun = () => {
    setConfig({ ...config, dry_run_mode: !config.dry_run_mode });
  };

  const toggleApproval = () => {
    setConfig({ ...config, require_approval: !config.require_approval });
  };

  return (
    <div className="space-y-6">
      {/* Agent Status */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-bold text-gray-900">Agent Status</h3>
            <div className="flex items-center space-x-3 mt-2">
              <Badge className={`${getAgentStateColor(config.state)} text-lg px-4 py-2`}>
                {config.state.toUpperCase()}
              </Badge>
              {config.dry_run_mode && (
                <Badge variant="warning">DRY RUN MODE</Badge>
              )}
              {config.require_approval && (
                <Badge variant="info">MANUAL APPROVAL REQUIRED</Badge>
              )}
            </div>
          </div>

          <div className={`w-24 h-24 rounded-full ${
            config.state === 'running' ? 'bg-success-100' :
            config.state === 'paused' ? 'bg-warning-100' : 'bg-gray-100'
          } flex items-center justify-center`}>
            <div className={`w-16 h-16 rounded-full ${
              config.state === 'running' ? 'bg-success-500 animate-pulse' :
              config.state === 'paused' ? 'bg-warning-500' : 'bg-gray-400'
            }`}></div>
          </div>
        </div>
      </Card>

      {/* Control Buttons */}
      <Card>
        <CardHeader title="Agent Controls" subtitle="Manage AI Agent operation state" />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button
            variant="success"
            size="lg"
            onClick={handleStart}
            disabled={config.state === 'running' || isUpdating}
            isLoading={isUpdating && config.state !== 'running'}
            className="w-full"
          >
            <Play className="w-5 h-5 mr-2" />
            Start Agent
          </Button>

          <Button
            variant="warning"
            size="lg"
            onClick={handlePause}
            disabled={config.state !== 'running' || isUpdating}
            isLoading={isUpdating && config.state === 'running'}
            className="w-full"
          >
            <Pause className="w-5 h-5 mr-2" />
            Pause Agent
          </Button>

          <Button
            variant="danger"
            size="lg"
            onClick={handleStop}
            disabled={config.state === 'stopped' || isUpdating}
            isLoading={isUpdating}
            className="w-full"
          >
            <StopCircle className="w-5 h-5 mr-2" />
            Stop Agent
          </Button>
        </div>

        {config.state === 'stopped' && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600">
              The agent is stopped. Click "Start Agent" to begin monitoring and processing errors.
            </p>
          </div>
        )}

        {config.dry_run_mode && config.state === 'running' && (
          <div className="mt-4 p-4 bg-warning-50 rounded-lg border border-warning-200 flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-warning-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-warning-800">Dry Run Mode Active</p>
              <p className="text-sm text-warning-700 mt-1">
                The agent is creating fix proposals but NOT executing them. This is safe for testing.
              </p>
            </div>
          </div>
        )}
      </Card>

      {/* Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Safety Settings */}
        <Card>
          <CardHeader title="Safety Settings" subtitle="Configure agent safety controls" />

          <div className="space-y-4">
            {/* Dry Run Mode */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-gray-900">Dry Run Mode</h4>
                <p className="text-sm text-gray-600 mt-1">
                  Create fix proposals without executing them
                </p>
              </div>
              <button
                onClick={toggleDryRun}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  config.dry_run_mode ? 'bg-warning-500' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    config.dry_run_mode ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Manual Approval */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-gray-900">Manual Approval Required</h4>
                <p className="text-sm text-gray-600 mt-1">
                  All fixes require manual approval before execution
                </p>
              </div>
              <button
                onClick={toggleApproval}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  config.require_approval ? 'bg-primary-500' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    config.require_approval ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </Card>

        {/* Operational Settings */}
        <Card>
          <CardHeader title="Operational Settings" subtitle="Configure agent behavior" />

          <div className="space-y-4">
            {/* Polling Interval */}
            <div>
              <label className="text-sm font-semibold text-gray-900 block mb-2">
                Polling Interval
              </label>
              <div className="flex items-center space-x-3">
                <input
                  type="number"
                  value={config.polling_interval_seconds / 60}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      polling_interval_seconds: parseInt(e.target.value) * 60,
                    })
                  }
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  min="1"
                  max="60"
                />
                <span className="text-sm text-gray-600">minutes</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">How often to check for new errors</p>
            </div>

            {/* Max Concurrent Fixes */}
            <div>
              <label className="text-sm font-semibold text-gray-900 block mb-2">
                Max Concurrent Fixes
              </label>
              <input
                type="number"
                value={config.max_concurrent_fixes}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    max_concurrent_fixes: parseInt(e.target.value),
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                min="1"
                max="10"
              />
              <p className="text-xs text-gray-500 mt-1">
                Maximum number of fixes to execute simultaneously
              </p>
            </div>

            <Button variant="primary" className="w-full mt-4">
              <Settings className="w-4 h-4 mr-2" />
              Save Configuration
            </Button>
          </div>
        </Card>
      </div>

      {/* Activity Log */}
      <Card>
        <CardHeader title="Recent Activity" subtitle="Latest agent actions and events" />

        <div className="space-y-3">
          {[
            { time: '2 minutes ago', action: 'Discovered new error', details: 'odometerError for driver John Smith' },
            { time: '5 minutes ago', action: 'Fix proposed', details: 'twoIdenticalStatusesError - awaiting approval' },
            { time: '10 minutes ago', action: 'Fix executed successfully', details: 'noPowerUpError for driver Mike Johnson' },
            { time: '15 minutes ago', action: 'Polling completed', details: 'Checked 150 logs, found 2 new errors' },
          ].map((log, index) => (
            <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
              <div className="w-2 h-2 rounded-full bg-primary-500 mt-2"></div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900">{log.action}</p>
                  <span className="text-xs text-gray-500">{log.time}</span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{log.details}</p>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
