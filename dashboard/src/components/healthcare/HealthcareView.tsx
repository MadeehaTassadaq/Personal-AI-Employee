import { useState, useEffect } from 'react';
import { useApi } from '../../hooks/useApi';
import { HealthcareStats } from '../../hooks/useApi';
import PatientDirectory from './PatientDirectory';
import AppointmentsCalendar from './AppointmentsCalendar';
import HealthcareStatsComponent from './HealthcareStats';

type HealthcareTab = 'directory' | 'appointments' | 'stats';

export default function HealthcareView() {
  const api = useApi();
  const [activeTab, setActiveTab] = useState<HealthcareTab>('directory');
  const [stats, setStats] = useState<HealthcareStats | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await api.fetchHealthcareStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load healthcare stats:', error);
    }
  };

  const tabs: { id: HealthcareTab; label: string; icon: string }[] = [
    { id: 'directory', label: 'Patients', icon: '👥' },
    { id: 'appointments', label: 'Appointments', icon: '📅' },
    { id: 'stats', label: 'Statistics', icon: '📊' },
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Healthcare Management</h1>
        <p className="text-gray-600">Manage patients, appointments, and medical records</p>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="mb-6">
          <HealthcareStatsComponent
            total_patients={stats.total_patients}
            high_risk_patients={stats.high_risk_patients}
            pregnant_patients={stats.pregnant_patients}
            today_appointments={stats.today_appointments}
            upcoming_appointments={stats.upcoming_appointments}
            pending_invoices={stats.pending_invoices}
          />
        </div>
      )}

      {/* Tabs */}
      <div className="mb-4 border-b border-gray-200">
        <div className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {activeTab === 'directory' && <PatientDirectory />}
      {activeTab === 'appointments' && <AppointmentsCalendar />}
      {activeTab === 'stats' && (
        <div className="space-y-6">
          <HealthcareStatsComponent
            total_patients={stats?.total_patients || 0}
            high_risk_patients={stats?.high_risk_patients || 0}
            pregnant_patients={stats?.pregnant_patients || 0}
            today_appointments={stats?.today_appointments || 0}
            upcoming_appointments={stats?.upcoming_appointments || 0}
            pending_invoices={stats?.pending_invoices || 0}
          />
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">Healthcare Overview</h2>
            <p className="text-gray-600">Select a tab above to view detailed information.</p>
          </div>
        </div>
      )}
    </div>
  );
}
