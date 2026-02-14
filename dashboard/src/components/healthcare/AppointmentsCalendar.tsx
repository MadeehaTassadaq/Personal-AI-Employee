import { useState, useEffect } from 'react';
import { useApi, Appointment } from '../../hooks/useApi';

export default function AppointmentsCalendar() {
  const api = useApi();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [view, setView] = useState<'upcoming' | 'today'>('upcoming');
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newAppointment, setNewAppointment] = useState({
    patient_id: 0,
    doctor_id: 0,
    appointment_date: new Date().toISOString().slice(0, 16),
    appointment_type: 'consultation',
    duration: 30,
    notes: ''
  });
  const [patients, setPatients] = useState<any[]>([]);
  const [doctors, setDoctors] = useState<any[]>([]);

  useEffect(() => {
    loadAppointments();
    loadPatientsAndDoctors();
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

  const loadPatientsAndDoctors = async () => {
    try {
      const patientsResult = await api.fetchHealthcarePatients('');
      setPatients(patientsResult.patients || []);
      // In a real app, doctors would come from a separate API
      // For now, we'll use a mock list
      setDoctors([
        { id: 1, name: 'Dr. Smith' },
        { id: 2, name: 'Dr. Johnson' }
      ]);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  const handleCreateAppointment = async () => {
    try {
      await api.createHealthcareAppointment(newAppointment);
      setShowCreateForm(false);
      setNewAppointment({
        patient_id: 0,
        doctor_id: 0,
        appointment_date: new Date().toISOString().slice(0, 16),
        appointment_type: 'consultation',
        duration: 30,
        notes: ''
      });
      await loadAppointments();
    } catch (error) {
      console.error('Failed to create appointment:', error);
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
          <button
            onClick={() => setShowCreateForm(true)}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            + New
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
          ))}

      {/* Create Appointment Form */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-6">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
            <h2 className="text-xl font-bold mb-4">Schedule New Appointment</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Patient</label>
                <select
                  value={newAppointment.patient_id}
                  onChange={(e) => setNewAppointment({...newAppointment, patient_id: parseInt(e.target.value)})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select Patient</option>
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Doctor</label>
                <select
                  value={newAppointment.doctor_id}
                  onChange={(e) => setNewAppointment({...newAppointment, doctor_id: parseInt(e.target.value)})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select Doctor</option>
                  {doctors.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date & Time</label>
                <input
                  type="datetime-local"
                  value={newAppointment.appointment_date}
                  onChange={(e) => setNewAppointment({...newAppointment, appointment_date: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={newAppointment.appointment_type}
                  onChange={(e) => setNewAppointment({...newAppointment, appointment_type: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="consultation">Consultation</option>
                  <option value="followup">Follow-up</option>
                  <option value="checkup">Check-up</option>
                  <option value="emergency">Emergency</option>
                  <option value="prenatal">Prenatal</option>
                  <option value="lab_test">Lab Test</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Duration (minutes)</label>
                <input
                  type="number"
                  min="15"
                  max="120"
                  value={newAppointment.duration}
                  onChange={(e) => setNewAppointment({...newAppointment, duration: parseInt(e.target.value) || 30})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={newAppointment.notes}
                  onChange={(e) => setNewAppointment({...newAppointment, notes: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  rows="3"
                />
              </div>
              <div className="flex justify-end gap-4 mt-6">
                <button
                  onClick={() => setShowCreateForm(false)}
                  className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateAppointment}
                  disabled={!newAppointment.patient_id || !newAppointment.doctor_id}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Appointment
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}
