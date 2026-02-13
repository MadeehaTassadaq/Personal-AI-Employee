import { useState, useEffect } from 'react';
import { useApi, Patient, Vitals, Invoice } from '../../hooks/useApi';

interface PatientProfileProps {
  patientId: number;
}

export default function PatientProfile({ patientId }: PatientProfileProps) {
  const api = useApi();

  const [patient, setPatient] = useState<Patient | null>(null);
  const [vitals, setVitals] = useState<Vitals[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'vitals' | 'billing'>('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [patientId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [patientData, vitalsData, invoicesData] = await Promise.all([
        api.fetchHealthcarePatient(patientId),
        api.fetchPatientVitals(patientId),
        api.fetchPatientInvoices(patientId),
      ]);
      setPatient(patientData);
      setVitals(vitalsData.vitals || []);
      setInvoices(invoicesData.invoices || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load patient data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center py-12 bg-red-50 rounded-lg">
          <p className="text-red-600">Error: {error}</p>
        </div>
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="p-6">
        <div className="text-center py-12 bg-white rounded-lg">
          <p className="text-gray-500">Patient not found</p>
        </div>
      </div>
    );
  }

  const getRiskBadge = (risk: string) => {
    const colors: Record<string, string> = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-red-100 text-red-800',
    };
    return colors[risk] || colors.low;
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{patient.name}</h1>
            <p className="text-gray-600">MRN: {patient.medical_record_number}</p>
          </div>
          <span className={`px-3 py-1 rounded text-sm font-medium ${getRiskBadge(patient.risk_category)}`}>
            {patient.risk_category.toUpperCase()} RISK
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-4 border-b border-gray-200">
        <div className="flex gap-4">
          {(['overview', 'vitals', 'billing'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 border-b-2 ${
                activeTab === tab ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-600'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">Basic Information</h2>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Age:</span>
                <span className="font-medium">{patient.age}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Blood Type:</span>
                <span className="font-medium">{patient.blood_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Phone:</span>
                <span className="font-medium">{patient.phone}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Email:</span>
                <span className="font-medium">{patient.email}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Visits:</span>
                <span className="font-medium">{patient.total_visits}</span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">Medical History</h2>
            <div className="space-y-4">
              <div>
                <span className="text-gray-600 text-sm">Allergies:</span>
                <p className="mt-1">{patient.allergies || 'None reported'}</p>
              </div>
              <div>
                <span className="text-gray-600 text-sm">Chronic Conditions:</span>
                <p className="mt-1">{patient.chronic_conditions || 'None reported'}</p>
              </div>
            </div>
          </div>

          {patient.pregnancy_status !== 'not_applicable' && (
            <div className="bg-pink-50 p-6 rounded-lg shadow border border-pink-200">
              <h2 className="text-lg font-semibold mb-4 text-pink-900">Pregnancy Status</h2>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Status:</span>
                  <span className="font-medium">{patient.pregnancy_status.replace('_', ' ')}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'vitals' && (
        <div className="grid gap-4">
          {vitals.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <p className="text-gray-500">No vitals recorded</p>
            </div>
          ) : (
            vitals.map((v) => (
              <div key={v.id} className="bg-white p-4 rounded-lg shadow">
                <div className="flex justify-between items-center mb-3">
                  <span className="font-semibold">{new Date(v.date_taken).toLocaleString()}</span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Temperature:</span>
                    <span className="font-medium ml-2">{v.temperature || 'N/A'}°C</span>
                  </div>
                  <div>
                    <span className="text-gray-600">BP:</span>
                    <span className="font-medium ml-2">
                      {v.blood_pressure_systolic || 'N/A'}/{v.blood_pressure_diastolic || 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Heart Rate:</span>
                    <span className="font-medium ml-2">{v.heart_rate || 'N/A'} bpm</span>
                  </div>
                  <div>
                    <span className="text-gray-600">BMI:</span>
                    <span className="font-medium ml-2">{v.bmi || 'N/A'}</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'billing' && (
        <div className="grid gap-4">
          {invoices.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <p className="text-gray-500">No invoices found</p>
            </div>
          ) : (
            invoices.map((inv) => (
              <div key={inv.id} className="bg-white p-4 rounded-lg shadow">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-semibold">{inv.name}</h3>
                    <p className="text-sm text-gray-600">Date: {inv.invoice_date}</p>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">${inv.amount_total?.toFixed(2) || '0.00'}</div>
                    <div className="text-sm text-gray-600">{inv.payment_state}</div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
