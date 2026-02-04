interface Watcher {
  name: string;
  status: 'running' | 'stopped' | 'error';
}

interface WatcherPanelProps {
  watchers: Record<string, 'running' | 'stopped' | 'error'>;
  onStart: (name: string) => void;
  onStop: (name: string) => void;
  onStartAll: () => void;
  onStopAll: () => void;
}

const WATCHER_NAMES = ['file', 'gmail', 'whatsapp', 'linkedin', 'facebook', 'instagram', 'twitter'];

export function WatcherPanel({ 
  watchers, 
  onStart, 
  onStop,
  onStartAll,
  onStopAll 
}: WatcherPanelProps) {
  const watcherList: Watcher[] = WATCHER_NAMES.map(name => ({
    name,
    status: watchers[name] || 'stopped'
  }));

  const runningCount = watcherList.filter(w => w.status === 'running').length;

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Watchers</h2>
        <div className="panel-actions">
          <span className="badge">{runningCount} active</span>
          <button className="btn btn-sm btn-success" onClick={onStartAll}>
            Start All
          </button>
          <button className="btn btn-sm btn-danger" onClick={onStopAll}>
            Stop All
          </button>
        </div>
      </div>
      <div className="watcher-list">
        {watcherList.map(watcher => (
          <div key={watcher.name} className="watcher-row">
            <span className={`status-dot ${watcher.status}`} />
            <span className="watcher-name">{watcher.name}</span>
            <span className="watcher-events">
              {watcher.status === 'running' ? 'Monitoring...' : 'Idle'}
            </span>
            {watcher.status === 'running' ? (
              <button 
                className="btn btn-sm btn-secondary"
                onClick={() => onStop(watcher.name)}
              >
                Stop
              </button>
            ) : (
              <button 
                className="btn btn-sm btn-primary"
                onClick={() => onStart(watcher.name)}
              >
                Start
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
