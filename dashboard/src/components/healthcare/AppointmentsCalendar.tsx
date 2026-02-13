import { useState, useEffect } from 'react';
import { useApi, Appointment } from '../../hooks/useApi';

export default function AppointmentsCalendar() {
  const api = useApi();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [view, setView] = useState<'upcoming' | 'today'>('upcoming');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAppointments();
  }, [view]);

  const loadAppointments = async () => {
    setLoading(true);
    try {
      const today = new Date().toISOString().split('T')[0];
      const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];

      const result = await api.fetchHealthcareAppointments(
        today,
        view === 'upcoming' ? '2025-12-31' : tomorrow
      );
      setAppointments(result.appointments || []);
    } catch (error) {
      console.error('Failed to load appointments:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'scheduled': return 'bg-blue-100 text-blue-800';
      case 'confirmed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-gray-100 text-gray-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      case 'no_show': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatPatientName = (patient: any): string => {
    if (Array.isArray(patient)) return patient[1];
    return 'Unknown Patient';
  };

  const formatDoctorName = (doctor: any): string => {
    if (Array.isArray(doctor)) return 'Dr. ' + doctor[1];
    return 'Unknown Doctor';
  };

  const formatDateTime = (dateStr: string): string => {
    return new Date(dateStr).toLocaleString();
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Appointments</h1>
          <p className="text-gray-600">Schedule and manage patient appointments</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setView('upcoming')}
            className={`px-4 py-2 rounded ${view === 'upcoming' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            Upcoming
          </button>
          <button
            onClick={() => setView('today')}
            className={`px-4 py-2 rounded ${view === 'today' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            Today
          </button>
        </div>
      </div>

      <div className="grid gap-4">
        {loading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading appointments...</p>
          </div>
        ) : appointments.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500">No appointments found</p>
          </div>
        ) : (
          appointments.map((apt) => (
            <div key={apt.id} className="bg-white p-4 rounded-lg shadow hover:shadow-md transition">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg text-gray-900">{apt.name}</h3>
                  <p className="text-sm text-gray-600">
                    {formatPatientName(apt.patient_id)} with {formatDoctorName(apt.doctor_id)}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    {formatDateTime(apt.appointment_date)}
                  </p>
                  <div className="mt-2 flex items-center gap-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusBadge(apt.status)}`}>
                      {apt.status.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500">
                      {apt.duration} minutes
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded hover:bg-blue-100">
                    View
                  </button>
                  <button className="px-3 py-1 text-sm bg-green-50 text-green-700 rounded hover:bg-green-100">
                    Complete
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
