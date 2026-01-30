import { useState, useEffect, useCallback } from 'react';

interface RalphStep {
  step_number: number;
  action: string;
  description: string;
  result?: string;
  duration_ms?: number;
}

interface RalphTask {
  task_id: string;
  file_path: string;
  title: string;
  status: string;
  current_step: number;
  total_steps: number;
  steps: RalphStep[];
  started_at?: string;
  completed_at?: string;
  error?: string;
}

interface RalphStatus {
  status: 'stopped' | 'running' | 'paused' | 'processing' | 'error' | 'awaiting_approval';
  current_task: RalphTask | null;
  tasks_completed: number;
  tasks_failed: number;
  steps_executed: number;
  started_at?: string;
  last_activity?: string;
  error_message?: string;
}

interface RalphControllerProps {
  fetchStatus: () => Promise<RalphStatus>;
  startRalph: () => Promise<void>;
  stopRalph: () => Promise<void>;
  pauseRalph: () => Promise<void>;
  resumeRalph: () => Promise<void>;
}

export function RalphController({
  fetchStatus,
  startRalph,
  stopRalph,
  pauseRalph,
  resumeRalph
}: RalphControllerProps) {
  const [status, setStatus] = useState<RalphStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadStatus = useCallback(async () => {
    try {
      const data = await fetchStatus();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load status');
    } finally {
      setIsLoading(false);
    }
  }, [fetchStatus]);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 2000);
    return () => clearInterval(interval);
  }, [loadStatus]);

  const handleAction = async (action: () => Promise<void>, name: string) => {
    setActionLoading(true);
    setError(null);
    try {
      await action();
      await loadStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${name}`);
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusColor = (s: string) => {
    switch (s) {
      case 'running':
      case 'processing':
        return 'var(--color-success)';
      case 'paused':
      case 'awaiting_approval':
        return 'var(--color-warning)';
      case 'error':
        return 'var(--color-danger)';
      default:
        return 'var(--color-text-muted)';
    }
  };

  const formatDuration = (startedAt?: string) => {
    if (!startedAt) return '-';
    try {
      const start = new Date(startedAt);
      const now = new Date();
      const diff = now.getTime() - start.getTime();
      const hours = Math.floor(diff / 3600000);
      const mins = Math.floor((diff % 3600000) / 60000);
      if (hours > 0) return `${hours}h ${mins}m`;
      return `${mins}m`;
    } catch {
      return '-';
    }
  };

  if (isLoading) {
    return (
      <div className="panel ralph-controller">
        <div className="panel-header">
          <h2>Ralph Wiggum Loop</h2>
        </div>
        <div className="loading-state">Loading...</div>
      </div>
    );
  }

  const isRunning = status?.status === 'running' || status?.status === 'processing';
  const isPaused = status?.status === 'paused';
  const isStopped = status?.status === 'stopped';

  return (
    <div className="panel ralph-controller">
      <div className="panel-header">
        <h2>Ralph Wiggum Loop</h2>
        <span
          className="ralph-status-badge"
          style={{ backgroundColor: getStatusColor(status?.status || 'stopped') }}
        >
          {status?.status?.toUpperCase() || 'STOPPED'}
        </span>
      </div>

      {error && <div className="ralph-error">{error}</div>}

      <div className="ralph-controls">
        {isStopped && (
          <button
            className="btn btn-success"
            onClick={() => handleAction(startRalph, 'start')}
            disabled={actionLoading}
          >
            Start Loop
          </button>
        )}
        {isRunning && (
          <>
            <button
              className="btn btn-warning"
              onClick={() => handleAction(pauseRalph, 'pause')}
              disabled={actionLoading}
            >
              Pause
            </button>
            <button
              className="btn btn-danger"
              onClick={() => handleAction(stopRalph, 'stop')}
              disabled={actionLoading}
            >
              Stop
            </button>
          </>
        )}
        {isPaused && (
          <>
            <button
              className="btn btn-success"
              onClick={() => handleAction(resumeRalph, 'resume')}
              disabled={actionLoading}
            >
              Resume
            </button>
            <button
              className="btn btn-danger"
              onClick={() => handleAction(stopRalph, 'stop')}
              disabled={actionLoading}
            >
              Stop
            </button>
          </>
        )}
      </div>

      <div className="ralph-stats">
        <div className="ralph-stat">
          <span className="stat-label">Tasks Completed</span>
          <span className="stat-value">{status?.tasks_completed || 0}</span>
        </div>
        <div className="ralph-stat">
          <span className="stat-label">Tasks Failed</span>
          <span className="stat-value error">{status?.tasks_failed || 0}</span>
        </div>
        <div className="ralph-stat">
          <span className="stat-label">Steps Executed</span>
          <span className="stat-value">{status?.steps_executed || 0}</span>
        </div>
        <div className="ralph-stat">
          <span className="stat-label">Uptime</span>
          <span className="stat-value">{formatDuration(status?.started_at)}</span>
        </div>
      </div>

      {status?.current_task && (
        <div className="ralph-current-task">
          <h3>Current Task</h3>
          <div className="task-info">
            <div className="task-title">{status.current_task.title}</div>
            <div className="task-progress">
              Step {status.current_task.current_step} of {status.current_task.total_steps}
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{
                  width: `${(status.current_task.current_step / Math.max(status.current_task.total_steps, 1)) * 100}%`
                }}
              />
            </div>
          </div>

          {status.current_task.steps.length > 0 && (
            <div className="task-steps">
              <h4>Recent Steps</h4>
              {status.current_task.steps.slice(-5).map((step) => (
                <div key={step.step_number} className={`step-item step-${step.result || 'pending'}`}>
                  <span className="step-number">#{step.step_number}</span>
                  <span className="step-action">{step.action}</span>
                  <span className="step-result">
                    {step.result || 'pending'}
                    {step.duration_ms && ` (${step.duration_ms}ms)`}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {status?.error_message && (
        <div className="ralph-error-detail">
          <strong>Error:</strong> {status.error_message}
        </div>
      )}
    </div>
  );
}
