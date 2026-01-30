import { useState, useEffect, useCallback } from 'react';

interface FinancialSummary {
  accounts_receivable: { total: number; count: number };
  accounts_payable: { total: number; count: number };
  month_revenue: number;
  cash_position: number | null;
  net_position: number;
  ar_ap_ratio: number;
  generated_at: string;
}

interface OdooStatus {
  status: string;
  server_version?: string;
  error?: string;
  checked_at: string;
}

interface OdooIntegrationProps {
  fetchOdooStatus: () => Promise<OdooStatus>;
  fetchFinancialSummary: () => Promise<FinancialSummary>;
}

export function OdooIntegration({
  fetchOdooStatus,
  fetchFinancialSummary
}: OdooIntegrationProps) {
  const [status, setStatus] = useState<OdooStatus | null>(null);
  const [summary, setSummary] = useState<FinancialSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const statusData = await fetchOdooStatus();
      setStatus(statusData);

      if (statusData.status === 'connected') {
        const summaryData = await fetchFinancialSummary();
        setSummary(summaryData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load Odoo data');
    } finally {
      setIsLoading(false);
    }
  }, [fetchOdooStatus, fetchFinancialSummary]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 300000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, [loadData]);

  const formatCurrency = (amount: number | null): string => {
    if (amount === null) return '--';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const getStatusColor = (): string => {
    if (!status) return 'var(--color-text-muted)';
    switch (status.status) {
      case 'connected': return 'var(--color-success)';
      case 'error': return 'var(--color-danger)';
      default: return 'var(--color-warning)';
    }
  };

  if (isLoading && !status) {
    return (
      <div className="panel odoo-panel">
        <div className="panel-header">
          <h3>Odoo Accounting</h3>
        </div>
        <div className="panel-content loading">
          Connecting to Odoo...
        </div>
      </div>
    );
  }

  return (
    <div className="panel odoo-panel">
      <div className="panel-header">
        <h3>Odoo Accounting</h3>
        <div className="panel-actions">
          <span
            className="status-indicator"
            style={{ backgroundColor: getStatusColor() }}
            title={status?.status || 'unknown'}
          />
          <span className="status-text">
            {status?.status === 'connected' ? status.server_version : status?.status}
          </span>
          <button className="btn-icon" onClick={loadData} title="Refresh">
            [R]
          </button>
        </div>
      </div>

      {error && (
        <div className="panel-error">
          {error}
        </div>
      )}

      <div className="panel-content">
        {status?.status !== 'connected' ? (
          <div className="odoo-disconnected">
            <p>Odoo is not connected.</p>
            {status?.error && <p className="error-detail">{status.error}</p>}
            <p className="hint">
              Make sure Odoo is running at the configured URL.
            </p>
          </div>
        ) : summary ? (
          <div className="financial-summary">
            <div className="summary-row">
              <div className="summary-card positive">
                <span className="card-label">Accounts Receivable</span>
                <span className="card-value">{formatCurrency(summary.accounts_receivable.total)}</span>
                <span className="card-detail">{summary.accounts_receivable.count} invoices</span>
              </div>

              <div className="summary-card negative">
                <span className="card-label">Accounts Payable</span>
                <span className="card-value">{formatCurrency(summary.accounts_payable.total)}</span>
                <span className="card-detail">{summary.accounts_payable.count} bills</span>
              </div>
            </div>

            <div className="summary-row">
              <div className="summary-card">
                <span className="card-label">Month Revenue</span>
                <span className="card-value">{formatCurrency(summary.month_revenue)}</span>
              </div>

              <div className="summary-card">
                <span className="card-label">Cash Position</span>
                <span className="card-value">{formatCurrency(summary.cash_position)}</span>
              </div>
            </div>

            <div className="summary-metrics">
              <div className="metric">
                <span className="metric-label">Net Position</span>
                <span className={`metric-value ${summary.net_position >= 0 ? 'positive' : 'negative'}`}>
                  {formatCurrency(summary.net_position)}
                </span>
              </div>
              <div className="metric">
                <span className="metric-label">AR/AP Ratio</span>
                <span className="metric-value">{summary.ar_ap_ratio.toFixed(2)}</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="loading">Loading financial data...</div>
        )}

        {summary?.generated_at && (
          <div className="panel-footer">
            Last updated: {new Date(summary.generated_at).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
}
