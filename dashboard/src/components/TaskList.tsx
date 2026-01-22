import { useState, useEffect } from 'react';

interface VaultFile {
  name: string;
  path?: string;
  modified?: string;
}

interface TaskListProps {
  title: string;
  folder: string;
  fetchFolder: (folder: string) => Promise<VaultFile[]>;
  emptyMessage?: string;
}

export function TaskList({ 
  title, 
  folder, 
  fetchFolder,
  emptyMessage = 'No tasks' 
}: TaskListProps) {
  const [files, setFiles] = useState<VaultFile[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadFiles = async () => {
      setLoading(true);
      const data = await fetchFolder(folder);
      // Filter out .gitkeep and convert to VaultFile format
      const taskFiles = (Array.isArray(data) ? data : [])
        .filter((f: string | VaultFile) => {
          const name = typeof f === 'string' ? f : f.name;
          return name !== '.gitkeep';
        })
        .map((f: string | VaultFile) => {
          if (typeof f === 'string') {
            return { name: f };
          }
          return f;
        });
      setFiles(taskFiles);
      setLoading(false);
    };
    loadFiles();
    const interval = setInterval(loadFiles, 10000);
    return () => clearInterval(interval);
  }, [folder, fetchFolder]);

  const getPriority = (name: string): 'high' | 'medium' | 'low' => {
    if (name.toLowerCase().includes('urgent')) return 'high';
    if (name.toLowerCase().includes('important')) return 'medium';
    return 'low';
  };

  const formatName = (name: string): string => {
    return name
      .replace('.md', '')
      .replace(/-/g, ' ')
      .replace(/_/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  if (loading) {
    return (
      <div className="panel">
        <div className="panel-header">
          <h2>{title}</h2>
        </div>
        <div className="empty-state">Loading...</div>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>{title}</h2>
        <span className="badge">{files.length}</span>
      </div>
      
      {files.length === 0 ? (
        <div className="empty-state">{emptyMessage}</div>
      ) : (
        <div className="task-list">
          {files.map((file, index) => {
            const priority = getPriority(file.name);
            return (
              <div key={index} className="task-item">
                <div className={`priority-indicator priority-${priority}`} />
                <div className="task-info">
                  <span className="task-title">{formatName(file.name)}</span>
                  <span className="task-status">{folder}</span>
                </div>
                {file.modified && (
                  <span className="task-date">
                    {new Date(file.modified).toLocaleDateString()}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
