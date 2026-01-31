import { useState } from 'react';
import { useApi } from './hooks/useApi';
import { StatusCard } from './components/StatusCard';
import { WatcherPanel } from './components/WatcherPanel';
import { ApprovalQueue } from './components/ApprovalQueue';
import { TaskList } from './components/TaskList';
import { PlatformCard } from './components/PlatformCard';
import { UnifiedFeed } from './components/UnifiedFeed';
import { AuditLog } from './components/AuditLog';
import { RalphController } from './components/RalphController';
import { SocialMediaDashboard } from './components/SocialMediaDashboard';
import { OdooIntegration } from './components/OdooIntegration';
import { BusinessAudit } from './components/BusinessAudit';
import { CalendarView } from './components/CalendarView';

type TabView = 'overview' | 'social' | 'finance' | 'audit';

function App() {
  const {
    status,
    error,
    startWatcher,
    stopWatcher,
    startAllWatchers,
    stopAllWatchers,
    fetchVaultFolder,
    fetchApprovals,
    approveItem,
    rejectItem,
    fetchActivity,
    fetchAudit,
    fetchAuditStats,
    fetchAuditAnalytics,
    fetchRalphStatus,
    startRalph,
    stopRalph,
    pauseRalph,
    resumeRalph,
    fetchCalendarStatus,
    fetchTodayEvents,
    fetchCalendarEvents
  } = useApi();

  const [activeTab, setActiveTab] = useState<TabView>('overview');

  const totalWatchers = Object.keys(status.watchers).length;
  const runningWatchers = Object.values(status.watchers).filter(
    s => s === 'running'
  ).length;

  // Platform data (derived from watcher status for now)
  const platforms = [
    {
      name: 'Gmail',
      icon: '[@]',
      status: status.watchers.gmail === 'running' ? 'healthy' : 'unknown',
      connected: status.watchers.gmail === 'running',
      eventsToday: 0
    },
    {
      name: 'WhatsApp',
      icon: '[#]',
      status: status.watchers.whatsapp === 'running' ? 'healthy' : 'unknown',
      connected: status.watchers.whatsapp === 'running',
      eventsToday: 0
    },
    {
      name: 'LinkedIn',
      icon: '[in]',
      status: status.watchers.linkedin === 'running' ? 'healthy' : 'unknown',
      connected: status.watchers.linkedin === 'running',
      eventsToday: 0
    },
    {
      name: 'Calendar',
      icon: '[CAL]',
      status: 'unknown',
      connected: false,
      eventsToday: 0
    }
  ] as const;

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <h1>Digital FTE Dashboard</h1>
          <span className="tier-badge">Gold</span>
        </div>
        <div className="header-right">
          <nav className="header-nav">
            <button
              className={`nav-btn ${activeTab === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button
              className={`nav-btn ${activeTab === 'audit' ? 'active' : ''}`}
              onClick={() => setActiveTab('audit')}
            >
              Audit Log
            </button>
          </nav>
          <div className="status-badge">
            <span className={`indicator ${status.system}`} />
            {status.system.toUpperCase()}
          </div>
        </div>
      </header>

      <main className="main">
        {error && (
          <div className="error-banner">
            Error: {error}
          </div>
        )}

        {activeTab === 'overview' && (
          <>
            {/* Status Cards Row */}
            <section className="status-section">
              <StatusCard
                title="System Status"
                value={status.system.toUpperCase()}
                status={status.system === 'running' ? 'running' : 'stopped'}
              />
              <StatusCard
                title="Active Watchers"
                value={`${runningWatchers}/${totalWatchers}`}
                status={runningWatchers > 0 ? 'running' : 'stopped'}
              />
              <StatusCard
                title="Pending Approvals"
                value={status.pending_approvals}
                status={status.pending_approvals > 0 ? 'warning' : 'running'}
              />
              <StatusCard
                title="Tasks Today"
                value="0"
                status="running"
              />
            </section>

            {/* Platform Cards Row */}
            <section className="platform-section">
              <h2 className="section-title">Platform Status</h2>
              <div className="platform-grid">
                {platforms.map((p) => (
                  <PlatformCard
                    key={p.name}
                    name={p.name}
                    icon={p.icon}
                    status={p.status as any}
                    connected={p.connected}
                    eventsToday={p.eventsToday}
                  />
                ))}
              </div>
            </section>

            <div className="panels">
              {/* Main Content Row */}
              <div className="panel-row">
                <WatcherPanel
                  watchers={status.watchers}
                  onStart={startWatcher}
                  onStop={stopWatcher}
                  onStartAll={startAllWatchers}
                  onStopAll={stopAllWatchers}
                />

                <CalendarView
                  fetchTodayEvents={fetchTodayEvents}
                  fetchEvents={fetchCalendarEvents}
                  fetchCalendarStatus={fetchCalendarStatus}
                />

                <RalphController
                  fetchStatus={fetchRalphStatus}
                  startRalph={startRalph}
                  stopRalph={stopRalph}
                  pauseRalph={pauseRalph}
                  resumeRalph={resumeRalph}
                />
              </div>

              {/* Approval and Tasks Row */}
              <div className="panel-row">
                <ApprovalQueue
                  fetchApprovals={fetchApprovals}
                  onApprove={approveItem}
                  onReject={rejectItem}
                />

                <TaskList
                  title="Needs Action"
                  folder="Needs_Action"
                  fetchFolder={fetchVaultFolder}
                  emptyMessage="No tasks pending action"
                />
              </div>

              {/* Task Lists Row */}
              <div className="panel-row three-col">
                <TaskList
                  title="Inbox"
                  folder="Inbox"
                  fetchFolder={fetchVaultFolder}
                  emptyMessage="No new tasks"
                />

                <TaskList
                  title="Pending Approval"
                  folder="Pending_Approval"
                  fetchFolder={fetchVaultFolder}
                  emptyMessage="No items awaiting approval"
                />

                <TaskList
                  title="Completed"
                  folder="Done"
                  fetchFolder={fetchVaultFolder}
                  emptyMessage="No completed tasks"
                />
              </div>

              {/* Unified Activity Feed */}
              <UnifiedFeed fetchActivity={fetchActivity} />
            </div>
          </>
        )}

        {activeTab === 'audit' && (
          <AuditLog fetchAudit={fetchAudit} />
        )}
      </main>

      <footer className="footer">
        Digital FTE Dashboard (Gold Tier) - {new Date().getFullYear()}
      </footer>
    </div>
  );
}

export default App;
