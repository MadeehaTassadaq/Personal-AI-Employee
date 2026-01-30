import { useState, useCallback } from 'react';

interface AuditReport {
  generated_at: string;
  platforms: Record<string, {
    status: string;
    healthy: boolean;
    error?: string;
  }>;
  financial?: {
    ar_total: number;
    ap_total: number;
    cash_position: number | null;
  };
  tasks?: {
    inbox: number;
    needs_action: number;
    pending_approval: number;
    done: number;
  };
}

interface BusinessAuditProps {
  fetchPlatformHealth: () => Promise<{
    overall: string;
    platforms: Record<string, { healthy: boolean; status: string; error?: string }>;
    checked_at: string;
  }>;
  fetchTaskStats: () => Promise<{
    inbox: number;
    needs_action: number;
    pending_approval: number;
    done: number;
  }>;
  generateReport?: () => Promise<{ report_path: string }>;
}

export function BusinessAudit({
  fetchPlatformHealth,
  fetchTaskStats,
  generateReport
}: BusinessAuditProps) {
  const [report, setReport] = useState<AuditReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runAudit = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [healthData, taskData] = await Promise.all([
        fetchPlatformHealth(),
        fetchTaskStats()
      ]);

      setReport({
        generated_at: healthData.checked_at,
        platforms: healthData.platforms,
        tasks: taskData
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run audit');
    } finally {
      setIsLoading(false);
    }
  }, [fetchPlatformHealth, fetchTaskStats]);

  const handleGenerateReport = async () => {
    if (!generateReport) return;

    try {
      setIsGenerating(true);
      const result = await generateReport();
      alert(`Report generated: ${result.report_path}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate report');
    } finally {
      setIsGenerating(false);
    }
  };

  const getOverallHealth = (): { status: string; color: string } => {
    if (!report) return { status: 'Unknown', color: 'var(--color-text-muted)' };

    const platforms = Object.values(report.platforms);
    const healthyCount = platforms.filter(p => p.healthy).length;

    if (healthyCount === platforms.length) {
      return { status: 'All Systems Healthy', color: 'var(--color-success)' };
    }
    if (healthyCount >= platforms.length / 2) {
      return { status: 'Partially Degraded', color: 'var(--color-warning)' };
    }
    return { status: 'Critical Issues', color: 'var(--color-danger)' };
  };

  const healthStatus = getOverallHealth();

  return (
    <div className="panel business-audit">
      <div className="panel-header">
        <h3>Business Audit</h3>
        <div className="panel-actions">
          <button
            className="btn-secondary"
            onClick={runAudit}
            disabled={isLoading}
          >
            {isLoading ? 'Running...' : 'Run Audit'}
          </button>
          {generateReport && (
            <button
              className="btn-primary"
              onClick={handleGenerateReport}
              disabled={isGenerating || !report}
            >
              {isGenerating ? 'Generating...' : 'Generate Report'}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="panel-error">
          {error}
        </div>
      )}

      <div className="panel-content">
        {!report ? (
          <div className="audit-empty">
            <p>No audit data available.</p>
            <p className="hint">Click "Run Audit" to check all platforms.</p>
          </div>
        ) : (
          <div className="audit-report">
            {/* Overall Status */}
            <div className="audit-status" style={{ borderLeftColor: healthStatus.color }}>
              <span className="status-label">Overall Status</span>
              <span className="status-value" style={{ color: healthStatus.color }}>
                {healthStatus.status}
              </span>
            </div>

            {/* Platform Status */}
            <div className="audit-section">
              <h4>Platform Health</h4>
              <div className="platform-list">
                {Object.entries(report.platforms).map(([name, status]) => (
                  <div key={name} className="platform-item">
                    <span className="platform-name">{name}</span>
                    <span
                      className={`platform-status ${status.healthy ? 'healthy' : 'unhealthy'}`}
                    >
                      {status.healthy ? '✓ Healthy' : '✗ ' + (status.error || status.status)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Task Status */}
            {report.tasks && (
              <div className="audit-section">
                <h4>Task Pipeline</h4>
                <div className="task-pipeline">
                  <div className="pipeline-stage">
                    <span className="stage-count">{report.tasks.inbox}</span>
                    <span className="stage-label">Inbox</span>
                  </div>
                  <span className="pipeline-arrow">→</span>
                  <div className="pipeline-stage">
                    <span className="stage-count">{report.tasks.needs_action}</span>
                    <span className="stage-label">In Progress</span>
                  </div>
                  <span className="pipeline-arrow">→</span>
                  <div className="pipeline-stage">
                    <span className="stage-count">{report.tasks.pending_approval}</span>
                    <span className="stage-label">Pending</span>
                  </div>
                  <span className="pipeline-arrow">→</span>
                  <div className="pipeline-stage">
                    <span className="stage-count">{report.tasks.done}</span>
                    <span className="stage-label">Done</span>
                  </div>
                </div>
              </div>
            )}

            <div className="panel-footer">
              Audit run: {new Date(report.generated_at).toLocaleString()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
