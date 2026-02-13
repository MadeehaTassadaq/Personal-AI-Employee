import { useState } from 'react';
import PatientDirectory from './PatientDirectory';
import AppointmentsCalendar from './AppointmentsCalendar';
import HealthcareStats from './HealthcareStats';

type HealthcareTab = 'directory' | 'appointments' | 'stats';

export default function HealthcareView() {
  const [activeTab, setActiveTab] = useState<HealthcareTab>('directory');

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
          <HealthcareStats />
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">Healthcare Overview</h2>
            <p className="text-gray-600">Select a tab above to view detailed information.</p>
          </div>
        </div>
      )}
    </div>
  );
}
