import { useState, useEffect } from 'react';
import { useApi, Patient } from '../../hooks/useApi';

export default function PatientDirectory() {
  const api = useApi();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newPatient, setNewPatient] = useState({
    name: '',
    phone: '',
    email: '',
    date_of_birth: '',
    blood_type: 'unknown',
    allergies: '',
    chronic_conditions: '',
    pregnancy_status: 'not_applicable',
    risk_category: 'low'
  });

  useEffect(() => {
    loadPatients();
  }, [searchTerm]);

  const loadPatients = async () => {
    setLoading(true);
    try {
      const result = await api.fetchHealthcarePatients(searchTerm);
      setPatients(result.patients || []);
    } catch (error) {
      console.error('Failed to load patients:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePatient = async () => {
    try {
      await api.createHealthcarePatient(newPatient);
      setShowCreateForm(false);
      setNewPatient({
        name: '',
        phone: '',
        email: '',
        date_of_birth: '',
        blood_type: 'unknown',
        allergies: '',
        chronic_conditions: '',
        pregnancy_status: 'not_applicable',
        risk_category: 'low'
      });
      await loadPatients();
    } catch (error) {
      console.error('Failed to create patient:', error);
    }
  };

  const getRiskBadgeColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Patient Directory</h1>
        <p className="text-gray-600">Manage patient profiles and medical records</p>
      </div>

      <div className="mb-4 flex gap-4">
        <input
          type="text"
          placeholder="Search patients by name, phone, or MRN..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={loadPatients}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Search
        </button>
        <button
          onClick={() => setShowCreateForm(true)}
          className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          + New Patient
        </button>
      </div>

      {/* Create Patient Form */}
      {showCreateForm && (
        <div className="mb-6 bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Create New Patient</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
              <input
                type="text"
                value={newPatient.name}
                onChange={(e) => setNewPatient({...newPatient, name: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input
                type="tel"
                value={newPatient.phone}
                onChange={(e) => setNewPatient({...newPatient, phone: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={newPatient.email}
                onChange={(e) => setNewPatient({...newPatient, email: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth</label>
              <input
                type="date"
                value={newPatient.date_of_birth}
                onChange={(e) => setNewPatient({...newPatient, date_of_birth: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Blood Type</label>
              <select
                value={newPatient.blood_type}
                onChange={(e) => setNewPatient({...newPatient, blood_type: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="unknown">Unknown</option>
                <option value="A+">A+</option>
                <option value="A-">A-</option>
                <option value="B+">B+</option>
                <option value="B-">B-</option>
                <option value="AB+">AB+</option>
                <option value="AB-">AB-</option>
                <option value="O+">O+</option>
                <option value="O-">O-</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Risk Category</label>
              <select
                value={newPatient.risk_category}
                onChange={(e) => setNewPatient({...newPatient, risk_category: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Allergies</label>
              <input
                type="text"
                value={newPatient.allergies}
                onChange={(e) => setNewPatient({...newPatient, allergies: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Chronic Conditions</label>
              <input
                type="text"
                value={newPatient.chronic_conditions}
                onChange={(e) => setNewPatient({...newPatient, chronic_conditions: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Pregnancy Status</label>
              <select
                value={newPatient.pregnancy_status}
                onChange={(e) => setNewPatient({...newPatient, pregnancy_status: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="not_applicable">Not Applicable</option>
                <option value="not_pregnant">Not Pregnant</option>
                <option value="pregnant">Pregnant</option>
                <option value="high_risk">High Risk</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-4 mt-6">
            <button
              onClick={() => setShowCreateForm(false)}
              className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              Cancel
            </button>
            <button
              onClick={handleCreatePatient}
              disabled={!newPatient.name || !newPatient.phone || !newPatient.email || !newPatient.date_of_birth}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Create Patient
            </button>
          </div>
        </div>
      )}

      <div className="grid gap-4">
        {loading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading patients...</p>
          </div>
        ) : patients.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500">No patients found</p>
          </div>
        ) : (
          patients.map((patient) => (
            <div key={patient.id} className="bg-white p-4 rounded-lg shadow hover:shadow-md transition">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-lg text-gray-900">{patient.name}</h3>
                  <p className="text-sm text-gray-600">MRN: {patient.medical_record_number}</p>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskBadgeColor(patient.risk_category)}`}>
                  {patient.risk_category.toUpperCase()} RISK
                </span>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-500">Phone:</span> {patient.phone}
                </div>
                <div>
                  <span className="text-gray-500">Age:</span> {patient.age}
                </div>
                <div>
                  <span className="text-gray-500">Blood Type:</span> {patient.blood_type}
                </div>
                <div>
                  <span className="text-gray-500">Visits:</span> {patient.total_visits}
                </div>
              </div>
              <div className="mt-3 flex gap-2">
                <button className="px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded hover:bg-blue-100">
                  View Profile
                </button>
                <button className="px-3 py-1 text-sm bg-green-50 text-green-700 rounded hover:bg-green-100">
                  Schedule Visit
                </button>
              </div>
            </div>
          ))
        )}
          </div>
        ) : patients.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500">No patients found</p>
          </div>
        ) : (
          patients.map((patient) => (
            <div key={patient.id} className="bg-white p-4 rounded-lg shadow hover:shadow-md transition">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-lg text-gray-900">{patient.name}</h3>
                  <p className="text-sm text-gray-600">MRN: {patient.medical_record_number}</p>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskBadgeColor(patient.risk_category)}`}>
                  {patient.risk_category.toUpperCase()} RISK
                </span>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-500">Phone:</span> {patient.phone}
                </div>
                <div>
                  <span className="text-gray-500">Age:</span> {patient.age}
                </div>
                <div>
                  <span className="text-gray-500">Blood Type:</span> {patient.blood_type}
                </div>
                <div>
                  <span className="text-gray-500">Visits:</span> {patient.total_visits}
                </div>
              </div>
              <div className="mt-3 flex gap-2">
                <button className="px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded hover:bg-blue-100">
                  View Profile
                </button>
                <button className="px-3 py-1 text-sm bg-green-50 text-green-700 rounded hover:bg-green-100">
                  Schedule Visit
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
