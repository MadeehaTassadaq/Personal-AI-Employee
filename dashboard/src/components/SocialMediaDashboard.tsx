import { useState, useEffect, useCallback } from 'react';

interface PlatformStats {
  platform: string;
  status: string;
  message?: string;
  followers?: number;
  engagement?: Record<string, number>;
}

interface SocialMediaDashboardProps {
  fetchSocialStats: () => Promise<{
    stats: PlatformStats[];
    generated_at: string;
  }>;
  fetchPlatformStatus: () => Promise<{
    platforms: Array<{
      platform: string;
      status: string;
      error?: string;
      last_check: string;
    }>;
    summary: { configured: number; total: number };
  }>;
}

export function SocialMediaDashboard({
  fetchSocialStats,
  fetchPlatformStatus
}: SocialMediaDashboardProps) {
  const [stats, setStats] = useState<PlatformStats[]>([]);
  const [platformStatus, setPlatformStatus] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [statsData, statusData] = await Promise.all([
        fetchSocialStats(),
        fetchPlatformStatus()
      ]);

      setStats(statsData.stats);
      setLastUpdated(statsData.generated_at);

      const statusMap: Record<string, string> = {};
      statusData.platforms.forEach(p => {
        statusMap[p.platform] = p.status;
      });
      setPlatformStatus(statusMap);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load social data');
    } finally {
      setIsLoading(false);
    }
  }, [fetchSocialStats, fetchPlatformStatus]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [loadData]);

  const getPlatformIcon = (platform: string): string => {
    const icons: Record<string, string> = {
      facebook: '[fb]',
      instagram: '[ig]',
      twitter: '[tw]',
      linkedin: '[in]'
    };
    return icons[platform] || '[?]';
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'configured':
      case 'connected':
        return 'var(--color-success)';
      case 'not_configured':
        return 'var(--color-text-muted)';
      case 'error':
        return 'var(--color-danger)';
      default:
        return 'var(--color-warning)';
    }
  };

  if (isLoading && stats.length === 0) {
    return (
      <div className="panel social-dashboard">
        <div className="panel-header">
          <h3>Social Media</h3>
        </div>
        <div className="panel-content loading">
          Loading social media data...
        </div>
      </div>
    );
  }

  const configuredCount = Object.values(platformStatus).filter(
    s => s === 'configured'
  ).length;

  return (
    <div className="panel social-dashboard">
      <div className="panel-header">
        <h3>Social Media</h3>
        <div className="panel-actions">
          <span className="badge">
            {configuredCount}/4 platforms
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
        <div className="social-grid">
          {['facebook', 'instagram', 'twitter', 'linkedin'].map(platform => {
            const stat = stats.find(s => s.platform === platform);
            const status = platformStatus[platform] || 'unknown';

            return (
              <div key={platform} className="social-card">
                <div className="social-header">
                  <span className="social-icon">{getPlatformIcon(platform)}</span>
                  <span className="social-name">{platform.charAt(0).toUpperCase() + platform.slice(1)}</span>
                  <span
                    className="status-dot"
                    style={{ backgroundColor: getStatusColor(status) }}
                    title={status}
                  />
                </div>

                <div className="social-stats">
                  {status === 'configured' ? (
                    <>
                      <div className="social-stat">
                        <span className="label">Status</span>
                        <span className="value">Ready</span>
                      </div>
                      <div className="social-stat">
                        <span className="label">Followers</span>
                        <span className="value">{stat?.followers || '--'}</span>
                      </div>
                    </>
                  ) : (
                    <div className="social-stat">
                      <span className="label">Status</span>
                      <span className="value muted">Not Configured</span>
                    </div>
                  )}
                </div>

                {stat?.message && (
                  <div className="social-message">
                    {stat.message}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {lastUpdated && (
          <div className="panel-footer">
            Last updated: {new Date(lastUpdated).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
}
