import { useState, useEffect } from 'react';

interface VaultFile {
  filename: string;
  path?: string;
  folder?: string;
  created?: string;
  priority?: string;
  status?: string;
  title?: string;
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
          const name = typeof f === 'string' ? f : f.filename;
          return name && name !== '.gitkeep';
        })
        .map((f: string | VaultFile) => {
          if (typeof f === 'string') {
            return { filename: f };
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

  const getPriority = (name: string | undefined): 'high' | 'medium' | 'low' => {
    if (!name || typeof name !== 'string') return 'low';
    if (name.toLowerCase().includes('urgent')) return 'high';
    if (name.toLowerCase().includes('important')) return 'medium';
    return 'low';
  };

  const formatName = (name: string | undefined): string => {
    if (!name || typeof name !== 'string') return '';
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
            if (!file.filename) return null; // Skip files without filenames
            const priority = getPriority(file.filename);
            return (
              <div key={index} className="task-item">
                <div className={`priority-indicator priority-${priority}`} />
                <div className="task-info">
                  <span className="task-title">{formatName(file.filename)}</span>
                  <span className="task-status">{folder}</span>
                </div>
                {file.modified && (
                  <span className="task-date">
                    {new Date(file.modified).toLocaleDateString()}
                  </span>
                )}
              </div>
            );
          }).filter(Boolean)} {/* Remove any null values from the map */}
        </div>
      )}
    </div>
  );
}
