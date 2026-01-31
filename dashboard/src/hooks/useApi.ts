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

export interface AuditEntry {
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

export interface RalphStatus {
  status: 'stopped' | 'running' | 'paused' | 'processing' | 'error' | 'awaiting_approval';
  current_task: any | null;
  tasks_completed: number;
  tasks_failed: number;
  steps_executed: number;
  started_at?: string;
  last_activity?: string;
  error_message?: string;
}

export interface PlatformStatus {
  name: string;
  health: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  connected: boolean;
  last_sync?: string;
  events_today: number;
  error_message?: string;
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
      const response = await fetch(`${API_BASE}/watchers/${name}/start`, {
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
      const response = await fetch(`${API_BASE}/watchers/${name}/stop`, {
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
      const response = await fetch(`${API_BASE}/vault/folder/${folder}`);
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
      const response = await fetch(`${API_BASE}/approvals/pending`);
      if (!response.ok) throw new Error('Failed to fetch approvals');
      const data = await response.json();
      return data.files || [];
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
      const response = await fetch(`${API_BASE}/vault/activity`);
      if (!response.ok) throw new Error('Failed to fetch activity');
      const data = await response.json();
      return data.entries || [];
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

  // Audit API methods
  const fetchAudit = async (params: {
    limit?: number;
    platform?: string;
    action?: string;
    days?: number;
  } = {}): Promise<{ entries: AuditEntry[]; count: number }> => {
    try {
      const searchParams = new URLSearchParams();
      if (params.limit) searchParams.set('limit', String(params.limit));
      if (params.platform) searchParams.set('platform', params.platform);
      if (params.action) searchParams.set('action', params.action);
      if (params.days) searchParams.set('days', String(params.days));

      const response = await fetch(`${API_BASE}/audit?${searchParams}`);
      if (!response.ok) throw new Error('Failed to fetch audit log');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return { entries: [], count: 0 };
    }
  };

  const fetchAuditStats = async (days: number = 7): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE}/audit/stats?days=${days}`);
      if (!response.ok) throw new Error('Failed to fetch audit stats');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return null;
    }
  };

  const fetchAuditAnalytics = async (days: number = 30): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE}/audit/analytics?days=${days}`);
      if (!response.ok) throw new Error('Failed to fetch audit analytics');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return null;
    }
  };

  // Ralph Wiggum API methods
  const fetchRalphStatus = async (): Promise<RalphStatus> => {
    try {
      const response = await fetch(`${API_BASE}/ralph/status`);
      if (!response.ok) throw new Error('Failed to fetch Ralph status');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return {
        status: 'stopped',
        current_task: null,
        tasks_completed: 0,
        tasks_failed: 0,
        steps_executed: 0
      };
    }
  };

  const startRalph = async () => {
    try {
      const response = await fetch(`${API_BASE}/ralph/start`, {
        method: 'POST'
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to start Ralph');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  const stopRalph = async () => {
    try {
      const response = await fetch(`${API_BASE}/ralph/stop`, {
        method: 'POST'
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to stop Ralph');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  const pauseRalph = async () => {
    try {
      const response = await fetch(`${API_BASE}/ralph/pause`, {
        method: 'POST'
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to pause Ralph');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  const resumeRalph = async () => {
    try {
      const response = await fetch(`${API_BASE}/ralph/resume`, {
        method: 'POST'
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to resume Ralph');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  // Social Media API methods
  const fetchSocialStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/social/stats`);
      if (!response.ok) throw new Error('Failed to fetch social stats');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return { stats: [], generated_at: new Date().toISOString() };
    }
  };

  const fetchSocialPlatformStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/social/status`);
      if (!response.ok) throw new Error('Failed to fetch platform status');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return { platforms: [], summary: { configured: 0, total: 4 } };
    }
  };

  const fetchSocialHealth = async () => {
    try {
      const response = await fetch(`${API_BASE}/social/health`);
      if (!response.ok) throw new Error('Failed to fetch social health');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return { overall: 'unknown', platforms: {}, checked_at: new Date().toISOString() };
    }
  };

  // Odoo API methods
  const fetchOdooStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/odoo/status`);
      if (!response.ok) throw new Error('Failed to fetch Odoo status');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return { status: 'error', error: err instanceof Error ? err.message : 'Unknown', checked_at: new Date().toISOString() };
    }
  };

  const fetchFinancialSummary = async () => {
    try {
      const response = await fetch(`${API_BASE}/odoo/summary`);
      if (!response.ok) throw new Error('Failed to fetch financial summary');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  const fetchOdooInvoices = async (params: { state?: string; type?: string; limit?: number } = {}) => {
    try {
      const searchParams = new URLSearchParams();
      if (params.state) searchParams.set('state', params.state);
      if (params.type) searchParams.set('invoice_type', params.type);
      if (params.limit) searchParams.set('limit', String(params.limit));

      const response = await fetch(`${API_BASE}/odoo/invoices?${searchParams}`);
      if (!response.ok) throw new Error('Failed to fetch invoices');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return { invoices: [], count: 0 };
    }
  };

  // Calendar API methods
  const fetchCalendarStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/calendar/status`);
      if (!response.ok) throw new Error('Failed to fetch calendar status');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return { status: 'error', configured: false };
    }
  };

  const fetchTodayEvents = async () => {
    try {
      const response = await fetch(`${API_BASE}/calendar/today`);
      if (!response.ok) throw new Error('Failed to fetch today\'s events');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return { date: new Date().toISOString().split('T')[0], events: [], count: 0 };
    }
  };

  const fetchCalendarEvents = async (days: number = 7) => {
    try {
      const response = await fetch(`${API_BASE}/calendar/events?days=${days}`);
      if (!response.ok) throw new Error('Failed to fetch calendar events');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return { days, events: [], count: 0 };
    }
  };

  // Task stats for business audit
  const fetchTaskStats = async () => {
    try {
      const folderMap: Record<string, string> = {
        'Inbox': 'inbox',
        'Needs_Action': 'needs_action',
        'Pending_Approval': 'pending_approval',
        'Done': 'done'
      };
      const counts: Record<string, number> = {};

      for (const [apiFolder, countKey] of Object.entries(folderMap)) {
        const files = await fetchVaultFolder(apiFolder);
        counts[countKey] = files.length;
      }

      return {
        inbox: counts.inbox || 0,
        needs_action: counts.needs_action || 0,
        pending_approval: counts.pending_approval || 0,
        done: counts.done || 0
      };
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return { inbox: 0, needs_action: 0, pending_approval: 0, done: 0 };
    }
  };

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
    triggerProcessing,
    // Gold tier - Audit
    fetchAudit,
    fetchAuditStats,
    fetchAuditAnalytics,
    // Gold tier - Ralph Wiggum
    fetchRalphStatus,
    startRalph,
    stopRalph,
    pauseRalph,
    resumeRalph,
    // Gold tier - Social Media
    fetchSocialStats,
    fetchSocialPlatformStatus,
    fetchSocialHealth,
    // Gold tier - Odoo
    fetchOdooStatus,
    fetchFinancialSummary,
    fetchOdooInvoices,
    // Gold tier - Business Audit
    fetchTaskStats,
    // Calendar
    fetchCalendarStatus,
    fetchTodayEvents,
    fetchCalendarEvents
  };
}
