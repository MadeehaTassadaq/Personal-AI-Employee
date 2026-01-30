interface PlatformCardProps {
  name: string;
  icon: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  connected: boolean;
  lastSync?: string;
  eventsToday: number;
  errorMessage?: string;
}

export function PlatformCard({
  name,
  icon,
  status,
  connected,
  lastSync,
  eventsToday,
  errorMessage
}: PlatformCardProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'healthy': return 'var(--color-success)';
      case 'degraded': return 'var(--color-warning)';
      case 'unhealthy': return 'var(--color-danger)';
      default: return 'var(--color-text-muted)';
    }
  };

  const formatLastSync = (timestamp?: string) => {
    if (!timestamp) return 'Never';
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diff = now.getTime() - date.getTime();

      if (diff < 60000) return 'Just now';
      if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
      if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
      return date.toLocaleDateString();
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="platform-card">
      <div className="platform-header">
        <span className="platform-icon">{icon}</span>
        <span className="platform-name">{name}</span>
        <span
          className="platform-status-dot"
          style={{ backgroundColor: getStatusColor() }}
          title={status}
        />
      </div>

      <div className="platform-stats">
        <div className="platform-stat">
          <span className="stat-label">Status</span>
          <span className={`stat-value status-${status}`}>
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        <div className="platform-stat">
          <span className="stat-label">Last Sync</span>
          <span className="stat-value">{formatLastSync(lastSync)}</span>
        </div>
        <div className="platform-stat">
          <span className="stat-label">Events Today</span>
          <span className="stat-value">{eventsToday}</span>
        </div>
      </div>

      {errorMessage && (
        <div className="platform-error">
          {errorMessage}
        </div>
      )}
    </div>
  );
}
