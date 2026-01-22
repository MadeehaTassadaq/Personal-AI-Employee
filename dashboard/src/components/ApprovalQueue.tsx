import { useState, useEffect } from 'react';

interface ApprovalItem {
  id: string;
  title: string;
  type: string;
  created: string;
  content: string;
}

interface ApprovalQueueProps {
  fetchApprovals: () => Promise<ApprovalItem[]>;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}

export function ApprovalQueue({ 
  fetchApprovals, 
  onApprove, 
  onReject 
}: ApprovalQueueProps) {
  const [items, setItems] = useState<ApprovalItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<ApprovalItem | null>(null);

  useEffect(() => {
    const loadItems = async () => {
      const data = await fetchApprovals();
      setItems(data);
    };
    loadItems();
    const interval = setInterval(loadItems, 10000);
    return () => clearInterval(interval);
  }, [fetchApprovals]);

  const handleApprove = (id: string) => {
    onApprove(id);
    setItems(items.filter(item => item.id !== id));
    setSelectedItem(null);
  };

  const handleReject = (id: string) => {
    onReject(id);
    setItems(items.filter(item => item.id !== id));
    setSelectedItem(null);
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'email': return '📧';
      case 'whatsapp': return '💬';
      case 'linkedin': return '💼';
      default: return '📋';
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Pending Approvals</h2>
        <span className="badge">{items.length}</span>
      </div>
      
      {items.length === 0 ? (
        <div className="empty-state">
          No pending approvals
        </div>
      ) : (
        <div className="approval-list">
          {items.map(item => (
            <div key={item.id} className="approval-item">
              <div className="approval-info">
                <span className="approval-title">
                  {getTypeIcon(item.type)} {item.title}
                </span>
                <span className="approval-date">
                  {formatDate(item.created)}
                </span>
              </div>
              <div className="approval-actions">
                <button 
                  className="btn btn-sm btn-secondary"
                  onClick={() => setSelectedItem(item)}
                >
                  View
                </button>
                <button 
                  className="btn btn-sm btn-success"
                  onClick={() => handleApprove(item.id)}
                >
                  Approve
                </button>
                <button 
                  className="btn btn-sm btn-danger"
                  onClick={() => handleReject(item.id)}
                >
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedItem && (
        <div className="modal-overlay" onClick={() => setSelectedItem(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selectedItem.title}</h3>
              <button 
                className="close-btn"
                onClick={() => setSelectedItem(null)}
              >
                ×
              </button>
            </div>
            <div className="modal-content">
              <pre>{selectedItem.content}</pre>
            </div>
            <div className="modal-footer">
              <button 
                className="btn btn-danger"
                onClick={() => handleReject(selectedItem.id)}
              >
                Reject
              </button>
              <button 
                className="btn btn-success"
                onClick={() => handleApprove(selectedItem.id)}
              >
                Approve
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
