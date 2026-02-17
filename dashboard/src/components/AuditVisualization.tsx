import React, { useState, useEffect } from 'react';
import { useApi, AuditEntry } from '../hooks/useApi';

interface AuditStats {
  total_entries: number;
  by_platform: Record<string, number>;
  by_action: Record<string, number>;
  by_level: Record<string, number>;
  by_actor: Record<string, number>;
  errors: number;
  warnings: number;
  daily_counts: Record<string, number>;
  trends: {
    activity_change_pct: number;
    direction: string;
  };
}

interface AuditAnalytics {
  period_start: string;
  period_end: string;
  peak_activity_times: Array<{hour: number; count: number}>;
  platform_usage_patterns: Record<string, any>;
  error_rate_by_platform: Record<string, number>;
  task_completion_rates: Record<string, number>;
  top_actions: Array<{action: string; count: number}>;
  anomalies: any[];
}

export const AuditVisualization: React.FC = () => {
  const { fetchAudit, fetchAuditStats, fetchAuditAnalytics } = useApi();
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [analytics, setAnalytics] = useState<AuditAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [daysFilter, setDaysFilter] = useState(7);

  useEffect(() => {
    loadData();
  }, [daysFilter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const auditResponse = await fetchAudit({ days: daysFilter });
      const statsResponse = await fetchAuditStats(daysFilter);
      const analyticsResponse = await fetchAuditAnalytics(daysFilter);

      setEntries(auditResponse.entries || []);
      setStats(statsResponse.stats || null);
      setAnalytics(analyticsResponse.analytics || null);
    } catch (error) {
      console.error('Error loading audit data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error':
        return '#ef4444'; // red-500
      case 'warning':
        return '#f59e0b'; // amber-500
      case 'critical':
        return '#dc2626'; // red-600
      default:
        return '#10b981'; // emerald-500
    }
  };

  const getPlatformColor = (platform: string) => {
    switch (platform) {
      case 'gmail':
        return '#ea4335'; // Google red
      case 'whatsapp':
        return '#25d366'; // WhatsApp green
      case 'linkedin':
        return '#0a66c2'; // LinkedIn blue
      case 'ralph':
        return '#8b5cf6'; // violet-500
      case 'system':
        return '#6b7280'; // gray-500
      default:
        return '#3b82f6'; // blue-500
    }
  };

  if (loading) {
    return (
      <div className="audit-visualization">
        <div className="loading">Loading audit data...</div>
      </div>
    );
  }

  return (
    <div className="audit-visualization">
      <div className="audit-controls">
        <label htmlFor="days-filter">Time Period:</label>
        <select
          id="days-filter"
          value={daysFilter}
          onChange={(e) => setDaysFilter(Number(e.target.value))}
        >
          <option value={1}>Last 24 hours</option>
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
        </select>
      </div>

      {stats && (
        <div className="audit-summary">
          <h3>Audit Summary</h3>
          <div className="summary-cards">
            <div className="summary-card">
              <div className="card-value">{stats.total_entries}</div>
              <div className="card-label">Total Events</div>
            </div>
            <div className="summary-card">
              <div className="card-value">{stats.errors}</div>
              <div className="card-label">Errors</div>
            </div>
            <div className="summary-card">
              <div className="card-value">{stats.warnings}</div>
              <div className="card-label">Warnings</div>
            </div>
            {stats.trends && (
              <div className="summary-card">
                <div className="card-value">
                  {stats.trends.activity_change_pct > 0 ? '+' : ''}
                  {stats.trends.activity_change_pct.toFixed(1)}%
                </div>
                <div className="card-label">
                  {stats.trends.direction} activity
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {stats && (
        <div className="audit-charts">
          <div className="chart-section">
            <h4>By Platform</h4>
            <div className="chart-bars">
              {Object.entries(stats.by_platform).map(([platform, count]) => (
                <div key={platform} className="bar-item">
                  <div className="bar-label">
                    <span
                      className="color-indicator"
                      style={{ backgroundColor: getPlatformColor(platform) }}
                    />
                    {platform}
                  </div>
                  <div className="bar-container">
                    <div
                      className="bar-fill"
                      style={{
                        width: `${(count / Math.max(...Object.values(stats.by_platform))) * 100}%`,
                        backgroundColor: getPlatformColor(platform)
                      }}
                    />
                    <div className="bar-count">{count}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="chart-section">
            <h4>By Log Level</h4>
            <div className="chart-bars">
              {Object.entries(stats.by_level).map(([level, count]) => (
                <div key={level} className="bar-item">
                  <div className="bar-label">
                    <span
                      className="color-indicator"
                      style={{ backgroundColor: getLevelColor(level) }}
                    />
                    {level}
                  </div>
                  <div className="bar-container">
                    <div
                      className="bar-fill"
                      style={{
                        width: `${(count / Math.max(...Object.values(stats.by_level))) * 100}%`,
                        backgroundColor: getLevelColor(level)
                      }}
                    />
                    <div className="bar-count">{count}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {analytics && (
        <div className="audit-analytics">
          <h3>Advanced Analytics</h3>

          <div className="analytics-grid">
            {analytics.top_actions.length > 0 && (
              <div className="analytics-section">
                <h4>Top Actions</h4>
                <ul className="top-actions-list">
                  {analytics.top_actions.slice(0, 5).map((item, index) => (
                    <li key={index} className="action-item">
                      <span className="action-name">{item.action}</span>
                      <span className="action-count">{item.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {analytics.peak_activity_times.length > 0 && (
              <div className="analytics-section">
                <h4>Peak Activity Times</h4>
                <div className="time-chart">
                  {analytics.peak_activity_times.slice(0, 5).map((item, index) => (
                    <div key={index} className="time-slot">
                      <div className="time-label">{item.hour}:00</div>
                      <div className="time-bar">
                        <div
                          className="time-fill"
                          style={{
                            height: `${Math.min((item.count / Math.max(...analytics.peak_activity_times.map(t => t.count))) * 100, 100)}%`
                          }}
                        />
                        <div className="time-count">{item.count}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {analytics.error_rate_by_platform && Object.keys(analytics.error_rate_by_platform).length > 0 && (
              <div className="analytics-section">
                <h4>Error Rates by Platform</h4>
                <div className="error-rates">
                  {Object.entries(analytics.error_rate_by_platform).map(([platform, rate]) => (
                    <div key={platform} className="error-rate-item">
                      <span className="platform-name">{platform}</span>
                      <span className={`rate-value ${rate > 5 ? 'high-error' : rate > 1 ? 'medium-error' : 'low-error'}`}>
                        {rate.toFixed(2)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="recent-entries">
        <h4>Recent Entries</h4>
        <div className="entries-list">
          {entries.slice(0, 10).map((entry, index) => (
            <div key={index} className="entry-item">
              <div className="entry-timestamp">{new Date(entry.timestamp).toLocaleString()}</div>
              <div className="entry-platform" style={{ color: getPlatformColor(entry.platform) }}>
                {entry.platform}
              </div>
              <div className="entry-action">{entry.action}</div>
              <div className="entry-level" style={{ color: getLevelColor(entry.level) }}>
                {entry.level}
              </div>
              <div className="entry-details">
                {entry.actor} • {entry.correlation_id.substring(0, 8)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};