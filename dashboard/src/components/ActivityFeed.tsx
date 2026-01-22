import { useState, useEffect } from 'react';

interface ActivityEvent {
  timestamp: string;
  watcher: string;
  event: string;
  file?: string;
}

interface ActivityFeedProps {
  fetchActivity: () => Promise<ActivityEvent[]>;
}

export function ActivityFeed({ fetchActivity }: ActivityFeedProps) {
  const [events, setEvents] = useState<ActivityEvent[]>([]);

  useEffect(() => {
    const loadEvents = async () => {
      const data = await fetchActivity();
      setEvents(data.slice(0, 20)); // Show last 20 events
    };
    loadEvents();
    const interval = setInterval(loadEvents, 5000);
    return () => clearInterval(interval);
  }, [fetchActivity]);

  const getEventIcon = (event: string, watcher: string): string => {
    if (event.includes('created') || event.includes('new')) return '📥';
    if (event.includes('moved') || event.includes('processed')) return '✅';
    if (event.includes('error')) return '❌';
    if (watcher.includes('gmail')) return '📧';
    if (watcher.includes('whatsapp')) return '💬';
    if (watcher.includes('linkedin')) return '💼';
    return '📋';
  };

  const formatTime = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diff = now.getTime() - date.getTime();

      if (diff < 60000) return 'Just now';
      if (diff < 3600000) return Math.floor(diff / 60000) + 'm ago';
      if (diff < 86400000) return Math.floor(diff / 3600000) + 'h ago';
      return date.toLocaleDateString();
    } catch {
      return timestamp;
    }
  };

  const formatEventText = (event: ActivityEvent): string => {
    let text = event.event.replace(/_/g, ' ');
    if (event.file) {
      text += `: ${event.file}`;
    }
    return text;
  };

  return (
    <div className="panel activity-section">
      <div className="panel-header">
        <h2>Activity Feed</h2>
        <span className="badge">{events.length} events</span>
      </div>

      {events.length === 0 ? (
        <div className="empty-state">No recent activity</div>
      ) : (
        <div className="activity-list">
          {events.map((event, index) => (
            <div key={index} className="activity-item">
              <span className="activity-icon">
                {getEventIcon(event.event, event.watcher)}
              </span>
              <div className="activity-content">
                <span className="activity-event">
                  {formatEventText(event)}
                </span>
                <span className="activity-watcher">
                  {event.watcher}
                </span>
              </div>
              <span className="activity-time">
                {formatTime(event.timestamp)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
