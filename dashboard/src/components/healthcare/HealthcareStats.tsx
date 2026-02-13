
interface HealthcareStatsProps {
  total_patients?: number;
  high_risk_patients?: number;
  pregnant_patients?: number;
  today_appointments?: number;
  upcoming_appointments?: number;
  pending_invoices?: number;
}

export default function HealthcareStats({
  total_patients = 0,
  high_risk_patients = 0,
  pregnant_patients = 0,
  today_appointments = 0,
  upcoming_appointments = 0,
  pending_invoices = 0,
}: HealthcareStatsProps) {
  const stats = [
    { label: 'Total Patients', value: total_patients, color: 'bg-blue-500', icon: '👥' },
    { label: 'High Risk', value: high_risk_patients, color: 'bg-red-500', icon: '⚠️' },
    { label: 'Pregnant', value: pregnant_patients, color: 'bg-pink-500', icon: '🤰' },
    { label: 'Today Appointments', value: today_appointments, color: 'bg-green-500', icon: '📅' },
    { label: 'Upcoming', value: upcoming_appointments, color: 'bg-yellow-500', icon: '📆' },
    { label: 'Pending Invoices', value: pending_invoices, color: 'bg-purple-500', icon: '💰' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {stats.map((stat) => (
        <div key={stat.label} className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">{stat.icon}</span>
            <div className={`w-2 h-2 rounded-full ${stat.color}`}></div>
          </div>
          <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
          <div className="text-sm text-gray-600">{stat.label}</div>
        </div>
      ))}
    </div>
  );
}
