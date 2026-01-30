import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';

interface PlatformHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  connected: boolean;
  last_sync?: string;
  events_today: number;
  error_message?: string;
  response_time?: number;
  uptime_percentage?: number;
}

interface HealthMetrics {
  platform: string;
  response_time_ms: number;
  uptime_24h: number;
  error_rate: number;
  last_check: string;
}

export const PlatformHealthMonitor: React.FC = () => {
  const { fetchAudit, fetchAuditStats, fetchAuditAnalytics } = useApi();
  const [platforms, setPlatforms] = useState<PlatformHealth[]>([]);
  const [healthMetrics, setHealthMetrics] = useState<HealthMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  useEffect(() => {
    loadHealthData();
    // Refresh every 30 seconds
    const interval = setInterval(loadHealthData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadHealthData = async () => {
    setLoading(true);
    try {
      // Simulate platform health data - in a real implementation, this would come from an API
      const mockPlatforms: PlatformHealth[] = [
        {
          name: 'Gmail',
          status: 'healthy',
          connected: true,
          events_today: 42,
          response_time: 125,
          uptime_percentage: 99.9
        },
        {
          name: 'WhatsApp',
          status: 'healthy',
          connected: true,
          events_today: 28,
          response_time: 89,
          uptime_percentage: 99.7
        },
        {
          name: 'LinkedIn',
          status: 'degraded',
          connected: true,
          events_today: 12,
          error_message: 'Rate limiting detected',
          response_time: 450,
          uptime_percentage: 98.2
        },
        {
          name: 'Ralph Wiggum',
          status: 'healthy',
          connected: true,
          events_today: 15,
          response_time: 67,
          uptime_percentage: 100
        }
      ];

      // Simulate health metrics data
      const mockMetrics: HealthMetrics[] = [
        {
          platform: 'Gmail',
          response_time_ms: 125,
          uptime_24h: 99.9,
          error_rate: 0.1,
          last_check: new Date(Date.now() - 120000).toISOString()
        },
        {
          platform: 'WhatsApp',
          response_time_ms: 89,
          uptime_24h: 99.7,
          error_rate: 0.2,
          last_check: new Date(Date.now() - 95000).toISOString()
        },
        {
          platform: 'LinkedIn',
          response_time_ms: 450,
          uptime_24h: 98.2,
          error_rate: 1.8,
          last_check: new Date(Date.now() - 80000).toISOString()
        },
        {
          platform: 'Ralph Wiggum',
          response_time_ms: 67,
          uptime_24h: 100,
          error_rate: 0,
          last_check: new Date(Date.now() - 60000).toISOString()
        }
      ];

      setPlatforms(mockPlatforms);
      setHealthMetrics(mockMetrics);
    } catch (error) {
      console.error('Error loading health data:', error);
    } finally {
      setLoading(false);
      setLastRefresh(new Date());
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return '#10b981'; // emerald-500
      case 'degraded':
        return '#f59e0b'; // amber-500
      case 'unhealthy':
        return '#ef4444'; // red-500
      default:
        return '#6b7280'; // gray-500
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return '✅';
      case 'degraded':
        return '⚠️';
      case 'unhealthy':
        return '❌';
      default:
        return '❓';
    }
  };

  if (loading) {
    return (
      <div className="platform-health-monitor">
        <div className="loading">Loading platform health data...</div>
      </div>
    );
  }

  return (
    <div className="platform-health-monitor">
      <div className="monitor-header">
        <h3>Platform Health Status</h3>
        <button className="btn btn-sm btn-secondary" onClick={loadHealthData}>
          Refresh
        </button>
      </div>

      <div className="platform-grid">
        {platforms.map((platform, index) => (
          <div key={index} className={`platform-card platform-${platform.status}`}>
            <div className="platform-header">
              <div className="platform-name">{platform.name}</div>
              <div className="platform-status" style={{ color: getStatusColor(platform.status) }}>
                {getStatusIcon(platform.status)} {platform.status.charAt(0).toUpperCase() + platform.status.slice(1)}
              </div>
            </div>

            <div className="platform-details">
              <div className="metric-row">
                <div className="metric-label">Status</div>
                <div className="metric-value">
                  {platform.connected ? 'Connected' : 'Disconnected'}
                </div>
              </div>

              <div className="metric-row">
                <div className="metric-label">Events Today</div>
                <div className="metric-value">{platform.events_today}</div>
              </div>

              {platform.response_time && (
                <div className="metric-row">
                  <div className="metric-label">Avg Response</div>
                  <div className="metric-value">{platform.response_time}ms</div>
                </div>
              )}

              {platform.uptime_percentage && (
                <div className="metric-row">
                  <div className="metric-label">Uptime</div>
                  <div className="metric-value">{platform.uptime_percentage}%</div>
                </div>
              )}

              {platform.error_message && (
                <div className="metric-row">
                  <div className="metric-label">Issue</div>
                  <div className="metric-value error">{platform.error_message}</div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="health-metrics">
        <h4>Detailed Metrics</h4>
        <table className="metrics-table">
          <thead>
            <tr>
              <th>Platform</th>
              <th>Response Time</th>
              <th>Uptime (24h)</th>
              <th>Error Rate</th>
              <th>Last Check</th>
            </tr>
          </thead>
          <tbody>
            {healthMetrics.map((metric, index) => (
              <tr key={index}>
                <td>{metric.platform}</td>
                <td>{metric.response_time_ms}ms</td>
                <td>{metric.uptime_24h}%</td>
                <td>{metric.error_rate}%</td>
                <td>{new Date(metric.last_check).toLocaleTimeString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="refresh-info">
        Last refreshed: {lastRefresh.toLocaleTimeString()}
      </div>
    </div>
  );
};