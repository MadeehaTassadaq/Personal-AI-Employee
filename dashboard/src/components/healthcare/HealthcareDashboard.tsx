import { useState, useEffect } from 'react';
import { useApi } from '../../hooks/useApi';

interface HealthcareStats {
  total_patients?: number;
  high_risk_patients?: number;
  pregnant_patients?: number;
  today_appointments?: number;
  upcoming_appointments?: number;
  pending_invoices?: number;
}

export default function HealthcareDashboard() {
  const api = useApi();
  const [stats, setStats] = useState<HealthcareStats | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setLoading(true);
    try {
      const data = await api.fetchHealthcareStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load healthcare stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading healthcare statistics...</p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-6">
        <div className="text-center py-8">
          <p className="text-gray-500">No statistics available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Healthcare Statistics</h1>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {/* Total Patients */}
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-gray-900">{stats?.total_patients || 0}</span>
            <span className="text-sm text-gray-600">Total Patients</span>
          </div>
        </div>

        {/* High Risk */}
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-gray-900">{stats?.high_risk_patients || 0}</span>
            <span className="text-sm text-gray-600">High Risk</span>
          </div>
        </div>

        {/* Pregnant */}
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-gray-900">{stats?.pregnant_patients || 0}</span>
            <span className="text-sm text-gray-600">Pregnant</span>
          </div>
        </div>

        {/* Today's Appointments */}
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-gray-900">{stats?.today_appointments || 0}</span>
            <span className="text-sm text-gray-600">Today</span>
          </div>
        </div>

        {/* Upcoming */}
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-gray-900">{stats?.upcoming_appointments || 0}</span>
            <span className="text-sm text-gray-600">Next 7 Days</span>
          </div>
        </div>

        {/* Pending Invoices */}
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-gray-900">{stats?.pending_invoices || 0}</span>
            <span className="text-sm text-gray-600">Pending Invoices</span>
          </div>
        </div>

        {/* Refresh Button */}
        <button
          onClick={loadStats}
          className="mt-6 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Refresh Statistics
        </button>
      </div>
    </div>
  );
}
