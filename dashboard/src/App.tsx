import { useState, useEffect } from 'react';
import { useApi } from './hooks/useApi';
import { UnifiedFeed } from './components/UnifiedFeed';
import { AuditLog } from './components/AuditLog';
import { SocialMediaDashboard } from './components/SocialMediaDashboard';
import { ComposePanel } from './components/ComposePanel';
import { CalendarView } from './components/CalendarView';

type TabView = 'dashboard' | 'inbox' | 'approvals' | 'social' | 'calendar' | 'compose' | 'audit' | 'settings';

interface NavItem {
  id: TabView;
  label: string;
  icon: string;
  badge?: number;
}

function App() {
  const {
    status,
    error,
    isDemo,
    startAllWatchers,
    stopAllWatchers,
    fetchActivity,
    fetchAudit,
    fetchSocialStats,
    fetchSocialPlatformStatus,
    submitPost
  } = useApi();

  const [activeTab, setActiveTab] = useState<TabView>('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Calculate summary stats
  const runningWatchers = Object.values(status.watchers).filter(s => s === 'running').length;
  const totalWatchers = Object.keys(status.watchers).length;

  const navItems: NavItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'inbox', label: 'Inbox', icon: '📥', badge: status.inbox_count || 0 },
    { id: 'approvals', label: 'Approvals', icon: '✅', badge: status.pending_approvals || 0 },
    { id: 'social', label: 'Social Media', icon: '📱' },
    { id: 'calendar', label: 'Calendar', icon: '📅' },
    { id: 'compose', label: 'Compose', icon: '✏️' },
    { id: 'audit', label: 'Audit Log', icon: '📋' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return '#22c55e';
      case 'stopped': return '#ef4444';
      case 'error': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-header">
          <div className="logo">
            <span className="logo-icon">🤖</span>
            {!sidebarCollapsed && <span className="logo-text">Digital FTE</span>}
          </div>
          <button
            className="collapse-btn"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            aria-label="Toggle sidebar"
          >
            {sidebarCollapsed ? '→' : '←'}
          </button>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(item => (
            <button
              key={item.id}
              className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
              title={item.label}
            >
              <span className="nav-icon">{item.icon}</span>
              {!sidebarCollapsed && (
                <>
                  <span className="nav-label">{item.label}</span>
                  {item.badge !== undefined && item.badge > 0 && (
                    <span className="nav-badge">{item.badge}</span>
                  )}
                </>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="system-status">
            <div
              className="status-dot"
              style={{ backgroundColor: getStatusColor(status.system) }}
            />
            {!sidebarCollapsed && (
              <span className="status-label">{status.system}</span>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Top Header */}
        <header className="top-header">
          <div className="header-left">
            <h1 className="page-title">{navItems.find(i => i.id === activeTab)?.label}</h1>
          </div>
          <div className="header-right">
            <div className="time-display">
              <div className="date">
                {currentTime.toLocaleDateString('en-US', {
                  weekday: 'long',
                  month: 'short',
                  day: 'numeric'
                })}
              </div>
              <div className="time">
                {currentTime.toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit'
                })}
              </div>
            </div>
            {isDemo && (
              <div className="demo-badge">
                🎭 Demo Mode
              </div>
            )}
          </div>
        </header>

        {/* Error Banner */}
        {error && (
          <div className="error-banner">
            <strong>⚠️ Error:</strong> {error}
          </div>
        )}

        {/* Content Area */}
        <div className="content-area">
          {activeTab === 'dashboard' && (
            <div className="dashboard-view">
              {/* Stats Cards */}
              <div className="stats-grid">
                <div className="stat-card urgent">
                  <div className="stat-icon">✅</div>
                  <div className="stat-content">
                    <div className="stat-value">{status.pending_approvals}</div>
                    <div className="stat-label">Pending Approvals</div>
                  </div>
                </div>

                <div className="stat-card success">
                  <div className="stat-icon">🟢</div>
                  <div className="stat-content">
                    <div className="stat-value">{runningWatchers}/{totalWatchers}</div>
                    <div className="stat-label">Active Services</div>
                  </div>
                </div>

                <div className="stat-card info">
                  <div className="stat-icon">📥</div>
                  <div className="stat-content">
                    <div className="stat-value">{status.inbox_count || 0}</div>
                    <div className="stat-label">New Tasks</div>
                  </div>
                </div>

                <div className="stat-card warning">
                  <div className="stat-icon">🔄</div>
                  <div className="stat-content">
                    <div className="stat-value">{status.needs_action_count || 0}</div>
                    <div className="stat-label">In Progress</div>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="quick-actions-card">
                <h2 className="card-title">Quick Actions</h2>
                <div className="quick-actions-grid">
                  <button
                    className="quick-action-btn primary"
                    onClick={() => setActiveTab('compose')}
                  >
                    <span className="action-icon">✏️</span>
                    <span className="action-text">Create Post</span>
                  </button>
                  <button
                    className="quick-action-btn success"
                    onClick={startAllWatchers}
                  >
                    <span className="action-icon">▶️</span>
                    <span className="action-text">Start All</span>
                  </button>
                  <button
                    className="quick-action-btn danger"
                    onClick={stopAllWatchers}
                  >
                    <span className="action-icon">⏸</span>
                    <span className="action-text">Stop All</span>
                  </button>
                </div>
              </div>

              {/* Platform Status */}
              <div className="platforms-card">
                <h2 className="card-title">Platform Status</h2>
                <div className="platforms-grid">
                  {Object.entries(status.watchers).map(([name, state]) => (
                    <div
                      key={name}
                      className="platform-item"
                      style={{ borderLeftColor: getStatusColor(state) }}
                    >
                      <span className="platform-name">
                        {name.charAt(0).toUpperCase() + name.slice(1)}
                      </span>
                      <span className={`platform-status platform-${state}`}>
                        {state}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recent Activity */}
              <div className="activity-card">
                <h2 className="card-title">Recent Activity</h2>
                <UnifiedFeed fetchActivity={fetchActivity} limit={5} />
              </div>
            </div>
          )}

          {activeTab === 'inbox' && (
            <div className="folder-view">
              <div className="folder-header">
                <h2>Inbox</h2>
                <span className="count-badge">{status.inbox_count || 0} items</span>
              </div>
              <div className="empty-state">
                📭 Inbox is empty. New tasks will appear here.
              </div>
            </div>
          )}

          {activeTab === 'approvals' && (
            <div className="folder-view">
              <div className="folder-header">
                <h2>Pending Approvals</h2>
                <span className="count-badge">{status.pending_approvals || 0} items</span>
              </div>
              <div className="empty-state">
                ✅ No pending approvals. You're all caught up!
              </div>
            </div>
          )}

          {activeTab === 'social' && (
            <SocialMediaDashboard
              fetchSocialStats={fetchSocialStats}
              fetchPlatformStatus={fetchSocialPlatformStatus}
            />
          )}

          {activeTab === 'calendar' && (
            <CalendarView />
          )}

          {activeTab === 'compose' && (
            <ComposePanel onSubmit={submitPost} />
          )}

          {activeTab === 'audit' && (
            <AuditLog fetchAudit={fetchAudit} />
          )}

          {activeTab === 'settings' && (
            <div className="settings-view">
              <h2>Settings</h2>
              <div className="settings-section">
                <h3>System Configuration</h3>
                <div className="setting-item">
                  <label>Vault Path</label>
                  <code>./AI_Employee_Vault</code>
                </div>
                <div className="setting-item">
                  <label>Dry Run Mode</label>
                  <span className="status-badge">{isDemo ? 'Enabled' : 'Disabled'}</span>
                </div>
                <div className="setting-item">
                  <label>Auto-start Watchers</label>
                  <span className="status-badge">Enabled</span>
                </div>
              </div>

              <div className="settings-section">
                <h3>Connected Platforms</h3>
                {Object.entries(status.watchers).map(([name, state]) => (
                  <div key={name} className="platform-setting">
                    <span>{name.charAt(0).toUpperCase() + name.slice(1)}</span>
                    <span className={`status-indicator status-${state}`}>
                      {state}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
