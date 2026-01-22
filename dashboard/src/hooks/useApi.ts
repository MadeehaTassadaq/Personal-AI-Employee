import { useState, useEffect, useCallback } from 'react';

const API_BASE = '/api';

export interface SystemStatus {
  system: 'running' | 'stopped';
  watchers: Record<string, 'running' | 'stopped' | 'error'>;
  pending_approvals: number;
}

export interface VaultFile {
  name: string;
  path: string;
  modified: string;
}

export interface ApprovalItem {
  id: string;
  title: string;
  type: string;
  created: string;
  content: string;
}

export interface ActivityEvent {
  timestamp: string;
  watcher: string;
  event: string;
  file?: string;
}

export function useApi() {
  const [status, setStatus] = useState<SystemStatus>({
    system: 'stopped',
    watchers: {},
    pending_approvals: 0
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/status`);
      if (!response.ok) throw new Error('Failed to fetch status');
      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  const startWatcher = async (name: string) => {
    try {
      const response = await fetch(`${API_BASE}/watcher/start/${name}`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to start watcher');
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const stopWatcher = async (name: string) => {
    try {
      const response = await fetch(`${API_BASE}/watcher/stop/${name}`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to stop watcher');
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const startAllWatchers = async () => {
    try {
      const response = await fetch(`${API_BASE}/watchers/start-all`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to start watchers');
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const stopAllWatchers = async () => {
    try {
      const response = await fetch(`${API_BASE}/watchers/stop-all`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to stop watchers');
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const fetchVaultFolder = async (folder: string): Promise<VaultFile[]> => {
    try {
      const response = await fetch(`${API_BASE}/vault/${folder}`);
      if (!response.ok) throw new Error(`Failed to fetch ${folder}`);
      const data = await response.json();
      return data.files || [];
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return [];
    }
  };

  const fetchApprovals = async (): Promise<ApprovalItem[]> => {
    try {
      const response = await fetch(`${API_BASE}/approvals`);
      if (!response.ok) throw new Error('Failed to fetch approvals');
      const data = await response.json();
      return data.items || [];
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return [];
    }
  };

  const approveItem = async (id: string) => {
    try {
      const response = await fetch(`${API_BASE}/approvals/${id}/approve`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to approve item');
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const rejectItem = async (id: string) => {
    try {
      const response = await fetch(`${API_BASE}/approvals/${id}/reject`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to reject item');
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const fetchActivity = async (): Promise<ActivityEvent[]> => {
    try {
      const response = await fetch(`${API_BASE}/activity`);
      if (!response.ok) throw new Error('Failed to fetch activity');
      const data = await response.json();
      return data.events || [];
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return [];
    }
  };

  const triggerProcessing = async () => {
    try {
      const response = await fetch(`${API_BASE}/trigger/process-inbox`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to trigger processing');
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  return {
    status,
    error,
    loading,
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
  };
}
