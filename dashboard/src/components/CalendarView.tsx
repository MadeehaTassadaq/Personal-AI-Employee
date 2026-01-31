import { useState, useEffect, useCallback } from 'react';

interface CalendarEvent {
  id: string;
  summary: string;
  start: string;
  end: string;
  location?: string;
  description?: string;
  attendees?: string[];
  html_link?: string;
  all_day: boolean;
}

interface CalendarViewProps {
  fetchTodayEvents: () => Promise<{ date: string; events: CalendarEvent[]; count: number }>;
  fetchEvents: (days: number) => Promise<{ days: number; events: CalendarEvent[]; count: number }>;
  fetchCalendarStatus: () => Promise<{ status: string; configured: boolean; error?: string }>;
}

type ViewMode = 'today' | 'week';

export function CalendarView({ fetchTodayEvents, fetchEvents, fetchCalendarStatus }: CalendarViewProps) {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>('today');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [calendarStatus, setCalendarStatus] = useState<{ status: string; configured: boolean } | null>(null);
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);

  const loadStatus = useCallback(async () => {
    try {
      const status = await fetchCalendarStatus();
      setCalendarStatus(status);
      return status.status === 'connected';
    } catch {
      setCalendarStatus({ status: 'error', configured: false });
      return false;
    }
  }, [fetchCalendarStatus]);

  const loadEvents = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      if (viewMode === 'today') {
        const data = await fetchTodayEvents();
        setEvents(data.events);
      } else {
        const data = await fetchEvents(7);
        setEvents(data.events);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load events');
    } finally {
      setIsLoading(false);
    }
  }, [viewMode, fetchTodayEvents, fetchEvents]);

  useEffect(() => {
    const init = async () => {
      const isConnected = await loadStatus();
      if (isConnected) {
        await loadEvents();
      } else {
        setIsLoading(false);
      }
    };
    init();
    // Only run once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (calendarStatus?.status === 'connected') {
      loadEvents();
    }
  }, [viewMode, calendarStatus, loadEvents]);

  const formatTime = (dateStr: string, allDay: boolean) => {
    if (allDay) return 'All day';
    try {
      const date = new Date(dateStr);
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch {
      return dateStr;
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const getEventTypeColor = (summary: string) => {
    const lower = summary.toLowerCase();
    if (lower.includes('meeting') || lower.includes('call')) return 'var(--color-info)';
    if (lower.includes('deadline') || lower.includes('due')) return 'var(--color-danger)';
    if (lower.includes('review') || lower.includes('standup')) return 'var(--color-warning)';
    if (lower.includes('lunch') || lower.includes('break')) return 'var(--color-success)';
    return 'var(--color-primary)';
  };

  const isEventSoon = (startStr: string) => {
    try {
      const start = new Date(startStr);
      const now = new Date();
      const diffMs = start.getTime() - now.getTime();
      const diffMins = diffMs / (1000 * 60);
      return diffMins > 0 && diffMins <= 30;
    } catch {
      return false;
    }
  };

  if (!calendarStatus || calendarStatus.status !== 'connected') {
    return (
      <div className="panel calendar-view">
        <div className="panel-header">
          <h2>Calendar</h2>
          <span className="calendar-icon">[CAL]</span>
        </div>
        <div className="calendar-not-configured">
          <div className="config-icon">[!]</div>
          <p>Calendar not configured</p>
          <p className="config-hint">
            Run <code>python scripts/calendar_oauth.py</code> to connect Google Calendar
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="panel calendar-view">
      <div className="panel-header">
        <h2>Calendar</h2>
        <div className="calendar-controls">
          <button
            className={`view-btn ${viewMode === 'today' ? 'active' : ''}`}
            onClick={() => setViewMode('today')}
          >
            Today
          </button>
          <button
            className={`view-btn ${viewMode === 'week' ? 'active' : ''}`}
            onClick={() => setViewMode('week')}
          >
            Week
          </button>
          <button
            className="refresh-btn"
            onClick={loadEvents}
            disabled={isLoading}
            title="Refresh"
          >
            [R]
          </button>
        </div>
      </div>

      {error && <div className="calendar-error">{error}</div>}

      {isLoading ? (
        <div className="loading-state">Loading events...</div>
      ) : events.length === 0 ? (
        <div className="empty-state">
          <span className="empty-icon">[OK]</span>
          <p>No events {viewMode === 'today' ? 'today' : 'this week'}</p>
        </div>
      ) : (
        <div className="calendar-events">
          {events.map((event) => {
            const isExpanded = expandedEvent === event.id;
            const isSoon = isEventSoon(event.start);

            return (
              <div
                key={event.id}
                className={`event-card ${isExpanded ? 'expanded' : ''} ${isSoon ? 'soon' : ''}`}
                onClick={() => setExpandedEvent(isExpanded ? null : event.id)}
              >
                <div className="event-header">
                  <div
                    className="event-color-bar"
                    style={{ backgroundColor: getEventTypeColor(event.summary) }}
                  />
                  <div className="event-main">
                    <div className="event-title">{event.summary}</div>
                    <div className="event-time">
                      {viewMode === 'week' && (
                        <span className="event-date">{formatDate(event.start)} </span>
                      )}
                      <span>{formatTime(event.start, event.all_day)}</span>
                      {!event.all_day && (
                        <span className="time-separator"> - </span>
                      )}
                      {!event.all_day && (
                        <span>{formatTime(event.end, event.all_day)}</span>
                      )}
                    </div>
                  </div>
                  {isSoon && <span className="soon-badge">Soon</span>}
                </div>

                {isExpanded && (
                  <div className="event-details">
                    {event.location && (
                      <div className="event-detail">
                        <span className="detail-label">Location:</span>
                        <span className="detail-value">{event.location}</span>
                      </div>
                    )}
                    {event.attendees && event.attendees.length > 0 && (
                      <div className="event-detail">
                        <span className="detail-label">Attendees:</span>
                        <span className="detail-value">
                          {event.attendees.slice(0, 3).join(', ')}
                          {event.attendees.length > 3 && ` +${event.attendees.length - 3} more`}
                        </span>
                      </div>
                    )}
                    {event.description && (
                      <div className="event-detail">
                        <span className="detail-label">Notes:</span>
                        <span className="detail-value">
                          {event.description.length > 150
                            ? event.description.substring(0, 150) + '...'
                            : event.description}
                        </span>
                      </div>
                    )}
                    {event.html_link && (
                      <a
                        href={event.html_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="event-link"
                        onClick={(e) => e.stopPropagation()}
                      >
                        Open in Google Calendar
                      </a>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="calendar-footer">
        <span className="event-count">
          {events.length} event{events.length !== 1 ? 's' : ''}
        </span>
      </div>
    </div>
  );
}
