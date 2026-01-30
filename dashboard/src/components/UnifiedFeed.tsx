import { useState, useEffect, useMemo } from 'react';
import { useWebSocket, WebSocketMessage } from '../hooks/useWebSocket';

interface UnifiedEvent {
  id: string;
  timestamp: string;
  platform: string;
  eventType: string;
  title: string;
  details?: Record<string, any>;
  icon: string;
}

interface UnifiedFeedProps {
  fetchActivity: () => Promise<any[]>;
}

export function UnifiedFeed({ fetchActivity }: UnifiedFeedProps) {
  const [historicalEvents, setHistoricalEvents] = useState<UnifiedEvent[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);

  const { isConnected, messages } = useWebSocket({
    onConnect: () => console.log('UnifiedFeed: WebSocket connected'),
    onDisconnect: () => console.log('UnifiedFeed: WebSocket disconnected')
  });

  // Load historical events on mount
  useEffect(() => {
    const loadEvents = async () => {
      setIsLoading(true);
      try {
        const data = await fetchActivity();
        const events = data.map((e, i) => ({
          id: `hist-${i}`,
          timestamp: e.timestamp,
          platform: e.watcher || 'system',
          eventType: e.event || 'activity',
          title: formatEventTitle(e),
          details: e,
          icon: getEventIcon(e.event, e.watcher)
        }));
        setHistoricalEvents(events);
      } catch (err) {
        console.error('Failed to load activity:', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadEvents();
  }, [fetchActivity]);

  // Convert WebSocket messages to unified events
  const wsEvents = useMemo(() => {
    return messages
      .filter(m => m.type !== 'connected' && m.type !== 'heartbeat' && m.type !== 'pong')
      .map((m, i) => ({
        id: `ws-${i}`,
        timestamp: m.timestamp,
        platform: extractPlatform(m),
        eventType: m.type,
        title: formatWsTitle(m),
        details: m.data,
        icon: getWsIcon(m.type)
      }));
  }, [messages]);

  // Combine and dedupe events
  const allEvents = useMemo(() => {
    const combined = [...wsEvents, ...historicalEvents];
    // Sort by timestamp descending
    combined.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    return combined.slice(0, 50);
  }, [wsEvents, historicalEvents]);

  // Filter events
  const filteredEvents = useMemo(() => {
    if (filter === 'all') return allEvents;
    return allEvents.filter(e => e.platform.toLowerCase().includes(filter.toLowerCase()));
  }, [allEvents, filter]);

  const platforms = ['all', 'gmail', 'whatsapp', 'linkedin', 'ralph', 'system'];

  return (
    <div className="panel unified-feed">
      <div className="panel-header">
        <div className="feed-header-left">
          <h2>Unified Activity Feed</h2>
          <span className={`connection-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? 'Live' : 'Reconnecting...'}
          </span>
        </div>
        <div className="feed-filters">
          {platforms.map(p => (
            <button
              key={p}
              className={`filter-btn ${filter === p ? 'active' : ''}`}
              onClick={() => setFilter(p)}
            >
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="loading-state">Loading activity...</div>
      ) : filteredEvents.length === 0 ? (
        <div className="empty-state">No activity to display</div>
      ) : (
        <div className="feed-list">
          {filteredEvents.map(event => (
            <div key={event.id} className="feed-item">
              <span className="feed-icon">{event.icon}</span>
              <div className="feed-content">
                <div className="feed-title">{event.title}</div>
                <div className="feed-meta">
                  <span className={`feed-platform platform-${event.platform.toLowerCase()}`}>
                    {event.platform}
                  </span>
                  <span className="feed-time">{formatTime(event.timestamp)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function formatEventTitle(event: any): string {
  let text = (event.event || 'activity').replace(/_/g, ' ');
  if (event.file) {
    text += `: ${event.file}`;
  }
  return text;
}

function formatWsTitle(message: WebSocketMessage): string {
  if (message.data?.title) return message.data.title;
  if (message.data?.message) return message.data.message;
  if (message.data?.task_id) return `Task: ${message.data.task_id}`;
  return message.type.replace(/_/g, ' ');
}

function extractPlatform(message: WebSocketMessage): string {
  if (message.type.startsWith('ralph_')) return 'ralph';
  if (message.type.startsWith('watcher_')) {
    return message.data?.watcher || 'system';
  }
  return message.data?.platform || 'system';
}

function getEventIcon(event: string, watcher: string): string {
  if (event?.includes('created') || event?.includes('new')) return '(+)';
  if (event?.includes('moved') || event?.includes('processed')) return '[v]';
  if (event?.includes('error')) return '[!]';
  if (watcher?.includes('gmail')) return '[@]';
  if (watcher?.includes('whatsapp')) return '[#]';
  if (watcher?.includes('linkedin')) return '[in]';
  return '[*]';
}

function getWsIcon(type: string): string {
  if (type.includes('start')) return '[>]';
  if (type.includes('complete')) return '[v]';
  if (type.includes('error') || type.includes('fail')) return '[!]';
  if (type.includes('pause')) return '[||]';
  if (type.includes('ralph')) return '[R]';
  return '[*]';
}

function formatTime(timestamp: string): string {
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
}
