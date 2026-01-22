interface StatusCardProps {
  title: string;
  value: string | number;
  status?: 'running' | 'stopped' | 'warning';
}

export function StatusCard({ title, value, status }: StatusCardProps) {
  return (
    <div className="status-card">
      {status && <div className={`indicator ${status}`} />}
      <h3>{title}</h3>
      <span className="value">{value}</span>
    </div>
  );
}
