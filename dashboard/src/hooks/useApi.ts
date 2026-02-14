import { useState, useEffect, useCallback } from 'react';

const API_BASE = '/api';

export interface SystemStatus {
  system: 'running' | 'stopped';
  watchers: Record<string, 'running' | 'stopped' | 'error'>;
  pending_approvals: number;
  inbox_count?: number;
  needs_action_count?: number;
}

export interface VaultFile {
  filename: string;
  path: string;
  folder: string;
  created?: string;
  priority?: string;
  status?: string;
  title?: string;
  modified?: string;
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
  details: Record<string, any>;
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

// Healthcare interfaces
export interface Patient {
  id: number;
  name: string;
  medical_record_number: string;
  phone: string;
  email: string;
  date_of_birth: string;
  age: number;
  blood_type: string;
  risk_category: 'low' | 'medium' | 'high';
  allergies: string;
  chronic_conditions: string;
  pregnancy_status: string;
  last_visit_date: string;
  next_appointment: string;
  total_visits: number;
}

export interface Appointment {
  id: number;
  name: string;
  patient_id: number | [number, string];
  doctor_id: number | [number, string];
  appointment_date: string;
  appointment_type: string;
  status: 'scheduled' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled' | 'no_show';
  duration: number;
  reminder_sent: boolean;
  notes: string;
}

export interface Vitals {
  id: number;
  patient_id: number;
  date_taken: string;
  temperature: number;
  blood_pressure_systolic: number;
  blood_pressure_diastolic: number;
  heart_rate: number;
  respiratory_rate: number;
  oxygen_saturation: number;
  weight: number;
  height: number;
  bmi: number;
  notes: string;
}

export interface Invoice {
  id: number;
  name: string;
  invoice_date: string;
  amount_total: number;
  state: string;
  payment_state: string;
}

export interface HealthcareStats {
  total_patients: number;
  high_risk_patients: number;
  pregnant_patients: number;
  today_appointments: number;
  upcoming_appointments: number;
  pending_invoices: number;
}

export function useApi() {
  const [status, setStatus] = useState<SystemStatus>({
    system: 'stopped',
    watchers: {},
    pending_approvals: 0,
    inbox_count: 0,
    needs_action_count: 0
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
      const files = data.files || [];
      return files.map((file: any) => ({
        filename: file.filename,
        path: file.path,
        folder: file.folder,
        created: file.created,
        priority: file.priority,
        status: file.status,
        title: file.title,
        modified: file.created
      }));
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
      const files = data.files || [];
      return files.map((file: any) => ({
        id: file.filename || file.id || '',
        title: file.title || file.filename || 'Untitled',
        type: file.type || 'unknown',
        created: file.created || new Date().toISOString(),
        content: file.content || ''
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return [];
    }
  };

  const approveItem = async (id: string) => {
    try {
      const response = await fetch(`${API_BASE}/approvals/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: id,
          approved: true
        })
      });
      if (!response.ok) throw new Error('Failed to approve item');
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const rejectItem = async (id: string) => {
    try {
      const response = await fetch(`${API_BASE}/approvals/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: id,
          approved: false
        })
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
      await fetchStatus();
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
      await fetchStatus();
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
      await fetchStatus();
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
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

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

  const fetchOdooInvoices = async (params: {
    state?: string;
    type?: string;
    limit?: number;
  } = {}) => {
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
      if (!response.ok) throw new Error("Failed to fetch today's events");
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

  // Compose API - Submit post for approval
  const submitPost = async (
    platform: string,
    content: string,
    options?: { imageUrl?: string; link?: string; recipient?: string; subject?: string }
  ) => {
    try {
      const response = await fetch(`${API_BASE}/compose`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          platform,
          content,
          image_url: options?.imageUrl,
          link: options?.link,
          recipient: options?.recipient,
          subject: options?.subject
        })
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to submit post');
      }
      await fetchStatus();
      return { success: true };
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  // AI Content Generation
  const generateAIContent = async (params: {
    platform: string;
    context: string;
    options?: { recipient?: string; subject?: string };
  }) => {
    try {
      const response = await fetch(`${API_BASE}/ai/generate-content`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params)
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to generate content');
      }
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
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

  // === Healthcare API methods ===

  // Patients
  const fetchHealthcarePatients = async (search?: string): Promise<{ patients: Patient[]; count: number }> => {
    try {
      const params = search ? `?search=${encodeURIComponent(search)}` : '';
      const response = await fetch(`${API_BASE}/healthcare/patients${params}`);
      if (!response.ok) throw new Error('Failed to fetch patients');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return { patients: [], count: 0 };
    }
  };

  const fetchHealthcarePatient = async (patientId: number): Promise<Patient> => {
    try {
      const response = await fetch(`${API_BASE}/healthcare/patients/${patientId}`);
      if (!response.ok) throw new Error('Failed to fetch patient');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  const createHealthcarePatient = async (data: {
    name: string;
    phone: string;
    email: string;
    date_of_birth: string;
    blood_type?: string;
    allergies?: string;
    chronic_conditions?: string;
    pregnancy_status?: string;
    risk_category?: string;
  }): Promise<Patient> => {
    try {
      const response = await fetch(`${API_BASE}/healthcare/patients`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create patient');
      }
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  const updateHealthcarePatient = async (patientId: number, data: Partial<Patient>): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE}/healthcare/patients/${patientId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to update patient');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  // Appointments
  const fetchHealthcareAppointments = async (
    fromDate: string,
    toDate: string,
    status?: string
  ): Promise<{ appointments: Appointment[]; count: number }> => {
    try {
      const params = new URLSearchParams({ from_date: fromDate, to_date: toDate });
      if (status) params.append('status', status);
      const response = await fetch(`${API_BASE}/healthcare/appointments?${params}`);
      if (!response.ok) throw new Error('Failed to fetch appointments');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return { appointments: [], count: 0 };
    }
  };

  const fetchUpcomingAppointments = async (days: number = 7): Promise<{ appointments: Appointment[]; count: number }> => {
    try {
      const response = await fetch(`${API_BASE}/healthcare/appointments/upcoming?days=${days}`);
      if (!response.ok) throw new Error('Failed to fetch upcoming appointments');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return { appointments: [], count: 0 };
    }
  };

  const createHealthcareAppointment = async (data: {
    patient_id: number;
    doctor_id: number;
    appointment_date: string;
    appointment_type?: string;
    duration?: number;
    notes?: string;
  }): Promise<Appointment> => {
    try {
      const response = await fetch(`${API_BASE}/healthcare/appointments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) {
        const result = await response.json();
        throw new Error(result.detail || 'Failed to create appointment');
      }
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  const updateAppointmentStatus = async (appointmentId: number, status: string): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE}/healthcare/appointments/${appointmentId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to update appointment');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  // Vitals
  const fetchPatientVitals = async (patientId: number): Promise<{ vitals: Vitals[]; count: number }> => {
    try {
      const response = await fetch(`${API_BASE}/healthcare/patients/${patientId}/vitals`);
      if (!response.ok) throw new Error('Failed to fetch patient vitals');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return { vitals: [], count: 0 };
    }
  };

  const recordVitals = async (patientId: number, data: Partial<Vitals>): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE}/healthcare/patients/${patientId}/vitals`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) {
        const result = await response.json();
        throw new Error(result.detail || 'Failed to record vitals');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  // Billing
  const createPatientInvoice = async (
    patientId: number,
    items: Array<{ description: string; amount: number; quantity?: number }>,
    date?: string
  ): Promise<Invoice> => {
    try {
      const response = await fetch(`${API_BASE}/healthcare/patients/${patientId}/invoice`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items, date })
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create invoice');
      }
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  const fetchPatientInvoices = async (patientId: number): Promise<{ invoices: Invoice[]; count: number }> => {
    try {
      const response = await fetch(`${API_BASE}/healthcare/patients/${patientId}/invoices`);
      if (!response.ok) throw new Error('Failed to fetch patient invoices');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return { invoices: [], count: 0 };
    }
  };

  // Healthcare stats
  const fetchHealthcareStats = async (): Promise<HealthcareStats> => {
    try {
      const response = await fetch(`${API_BASE}/healthcare/stats`);
      if (!response.ok) throw new Error('Failed to fetch healthcare stats');
      return await response.json();
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
    fetchAudit,
    fetchAuditStats,
    fetchAuditAnalytics,
    fetchRalphStatus,
    startRalph,
    stopRalph,
    pauseRalph,
    resumeRalph,
    fetchSocialStats,
    fetchSocialPlatformStatus,
    fetchSocialHealth,
    fetchOdooStatus,
    fetchFinancialSummary,
    fetchOdooInvoices,
    fetchCalendarStatus,
    fetchTodayEvents,
    fetchCalendarEvents,
    submitPost,
    fetchTaskStats,
    generateAIContent,
    // Healthcare
    fetchHealthcarePatients,
    fetchHealthcarePatient,
    createHealthcarePatient,
    updateHealthcarePatient,
    fetchHealthcareAppointments,
    fetchUpcomingAppointments,
    createHealthcareAppointment,
    updateAppointmentStatus,
    fetchPatientVitals,
    recordVitals,
    createPatientInvoice,
    fetchPatientInvoices,
    fetchHealthcareStats
  };
}
