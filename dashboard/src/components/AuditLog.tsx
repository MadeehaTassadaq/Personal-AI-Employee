import { useState, useEffect, useCallback } from 'react';
import { AuditVisualization } from './AuditVisualization';

interface AuditEntry {
  timestamp: string;
  correlation_id: string;
  action: string;
  level: string;
  platform: string;
  actor: string;
  details?: Record<string, any>;
  task_id?: string;
  file_path?: string;
  duration_ms?: number;
}

interface AuditLogProps {
  fetchAudit: (params: {
    limit?: number;
    platform?: string;
    action?: string;
    days?: number;
  }) => Promise<{ entries: AuditEntry[]; count: number }>;
}

export function AuditLog({ fetchAudit }: AuditLogProps) {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEntry, setSelectedEntry] = useState<AuditEntry | null>(null);

  // Filters
  const [platformFilter, setPlatformFilter] = useState<string>('');
  const [levelFilter, setLevelFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [daysFilter, setDaysFilter] = useState<number>(7);

  const loadAudit = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await fetchAudit({
        limit: 100,
        platform: platformFilter || undefined,
        days: daysFilter
      });
      setEntries(result.entries || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit log');
    } finally {
      setIsLoading(false);
    }
  }, [fetchAudit, platformFilter, daysFilter]);

  useEffect(() => {
    loadAudit();
  }, [loadAudit]);

  // Filter entries locally
  const filteredEntries = entries.filter(entry => {
    if (levelFilter && entry.level !== levelFilter) return false;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      return (
        entry.action.toLowerCase().includes(term) ||
        entry.correlation_id.toLowerCase().includes(term) ||
        entry.platform.toLowerCase().includes(term) ||
        entry.task_id?.toLowerCase().includes(term) ||
        JSON.stringify(entry.details).toLowerCase().includes(term)
      );
    }
    return true;
  });

  const getLevelClass = (level: string) => {
    switch (level) {
      case 'error':
      case 'critical':
        return 'level-error';
      case 'warning':
        return 'level-warning';
      default:
        return 'level-info';
    }
  };

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const [activeTab, setActiveTab] = useState<'raw' | 'visual'>('visual');

  return (
    <div className="panel audit-log">
      <div className="panel-header">
        <div className="panel-tabs">
          <button
            className={`tab-btn ${activeTab === 'visual' ? 'active' : ''}`}
            onClick={() => setActiveTab('visual')}
          >
            Visualization
          </button>
          <button
            className={`tab-btn ${activeTab === 'raw' ? 'active' : ''}`}
            onClick={() => setActiveTab('raw')}
          >
            Raw Logs
          </button>
        </div>
        <button className="btn btn-sm btn-secondary" onClick={loadAudit}>
          Refresh
        </button>
      </div>

      <div className="audit-filters">
        <input
          type="text"
          placeholder="Search..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="audit-search"
        />
        <select
          value={platformFilter}
          onChange={(e) => setPlatformFilter(e.target.value)}
          className="audit-filter-select"
        >
          <option value="">All Platforms</option>
          <option value="gmail">Gmail</option>
          <option value="whatsapp">WhatsApp</option>
          <option value="linkedin">LinkedIn</option>
          <option value="ralph">Ralph</option>
          <option value="system">System</option>
        </select>
        <select
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
          className="audit-filter-select"
        >
          <option value="">All Levels</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
          <option value="critical">Critical</option>
        </select>
        <select
          value={daysFilter}
          onChange={(e) => setDaysFilter(Number(e.target.value))}
          className="audit-filter-select"
        >
          <option value={1}>Last 24h</option>
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
        </select>
      </div>

      {activeTab === 'visual' ? (
        <AuditVisualization />
      ) : (
        <>
          <div className="audit-filters">
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="audit-search"
            />
            <select
              value={platformFilter}
              onChange={(e) => setPlatformFilter(e.target.value)}
              className="audit-filter-select"
            >
              <option value="">All Platforms</option>
              <option value="gmail">Gmail</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="linkedin">LinkedIn</option>
              <option value="ralph">Ralph</option>
              <option value="system">System</option>
            </select>
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="audit-filter-select"
            >
              <option value="">All Levels</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
              <option value="critical">Critical</option>
            </select>
            <select
              value={daysFilter}
              onChange={(e) => setDaysFilter(Number(e.target.value))}
              className="audit-filter-select"
            >
              <option value={1}>Last 24h</option>
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
            </select>
          </div>

          {error && <div className="audit-error">{error}</div>}

          {isLoading ? (
            <div className="loading-state">Loading audit log...</div>
          ) : filteredEntries.length === 0 ? (
            <div className="empty-state">No audit entries found</div>
          ) : (
            <div className="audit-list">
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>ID</th>
                    <th>Action</th>
                    <th>Platform</th>
                    <th>Level</th>
                    <th>Actor</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEntries.map((entry, idx) => (
                    <tr
                      key={`${entry.correlation_id}-${idx}`}
                      className={`audit-row ${getLevelClass(entry.level)}`}
                      onClick={() => setSelectedEntry(entry)}
                    >
                      <td className="audit-time">{formatTime(entry.timestamp)}</td>
                      <td className="audit-id">{entry.correlation_id}</td>
                      <td className="audit-action">{entry.action.replace(/_/g, ' ')}</td>
                      <td className="audit-platform">{entry.platform}</td>
                      <td className={`audit-level ${getLevelClass(entry.level)}`}>
                        {entry.level}
                      </td>
                      <td className="audit-actor">{entry.actor}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* Detail Modal - only show for raw logs view */}
      {selectedEntry && activeTab === 'raw' && (
        <div className="modal-overlay" onClick={() => setSelectedEntry(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Audit Entry Details</h3>
              <button className="close-btn" onClick={() => setSelectedEntry(null)}>
                x
              </button>
            </div>
            <div className="modal-content">
              <div className="detail-row">
                <strong>Correlation ID:</strong> {selectedEntry.correlation_id}
              </div>
              <div className="detail-row">
                <strong>Timestamp:</strong> {formatTime(selectedEntry.timestamp)}
              </div>
              <div className="detail-row">
                <strong>Action:</strong> {selectedEntry.action}
              </div>
              <div className="detail-row">
                <strong>Platform:</strong> {selectedEntry.platform}
              </div>
              <div className="detail-row">
                <strong>Level:</strong> {selectedEntry.level}
              </div>
              <div className="detail-row">
                <strong>Actor:</strong> {selectedEntry.actor}
              </div>
              {selectedEntry.task_id && (
                <div className="detail-row">
                  <strong>Task ID:</strong> {selectedEntry.task_id}
                </div>
              )}
              {selectedEntry.file_path && (
                <div className="detail-row">
                  <strong>File:</strong> {selectedEntry.file_path}
                </div>
              )}
              {selectedEntry.duration_ms && (
                <div className="detail-row">
                  <strong>Duration:</strong> {selectedEntry.duration_ms}ms
                </div>
              )}
              {selectedEntry.details && Object.keys(selectedEntry.details).length > 0 && (
                <div className="detail-row">
                  <strong>Details:</strong>
                  <pre>{JSON.stringify(selectedEntry.details, null, 2)}</pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
