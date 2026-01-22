import { useApi } from './hooks/useApi';
import { StatusCard } from './components/StatusCard';
import { WatcherPanel } from './components/WatcherPanel';
import { ApprovalQueue } from './components/ApprovalQueue';
import { TaskList } from './components/TaskList';
import { ActivityFeed } from './components/ActivityFeed';

function App() {
  const {
    status,
    error,
    fetchStatus,
    startWatcher,
    stopWatcher,
    startAllWatchers,
    stopAllWatchers,
    fetchVaultFolder,
    fetchApprovals,
    approveItem,
    rejectItem,
    fetchActivity,
    triggerProcessing
  } = useApi();

  const totalWatchers = Object.keys(status.watchers).length;
  const runningWatchers = Object.values(status.watchers).filter(
    s => s === 'running'
  ).length;

  return (
    <div className="app">
      <header className="header">
        <h1>Digital FTE Dashboard</h1>
        <div className="status-badge">
          <span className={`indicator ${status.system}`} />
          {status.system.toUpperCase()}
        </div>
      </header>

      <main className="main">
        {error && (
          <div className="error-banner">
            Error: {error}
          </div>
        )}

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
            title="Tasks Processed" 
            value="0" 
            status="running" 
          />
        </section>

        <div className="panels">
          <div className="panel-row">
            <WatcherPanel
              watchers={status.watchers}
              onStart={startWatcher}
              onStop={stopWatcher}
              onStartAll={startAllWatchers}
              onStopAll={stopAllWatchers}
            />
            
            <ApprovalQueue
              fetchApprovals={fetchApprovals}
              onApprove={approveItem}
              onReject={rejectItem}
            />
          </div>

          <div className="panel-row">
            <TaskList
              title="Inbox"
              folder="inbox"
              fetchFolder={fetchVaultFolder}
              emptyMessage="No new tasks"
            />

            <TaskList
              title="Needs Action"
              folder="needs-action"
              fetchFolder={fetchVaultFolder}
              emptyMessage="No tasks pending action"
            />

            <TaskList
              title="Completed"
              folder="done"
              fetchFolder={fetchVaultFolder}
              emptyMessage="No completed tasks"
            />
          </div>

          <ActivityFeed fetchActivity={fetchActivity} />
        </div>
      </main>

      <footer className="footer">
        Digital FTE Dashboard • {new Date().getFullYear()}
      </footer>
    </div>
  );
}

export default App;
