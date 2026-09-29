import React, { useState } from 'react';
import { ComplaintResponse, Status } from '../types';
import StatusBadge from './StatusBadge';
import { updateStatus } from '../api/client';

interface Props {
  complaints: ComplaintResponse[];
  onStatusUpdate: () => void;
}

const ComplaintList: React.FC<Props> = ({ complaints, onStatusUpdate }) => {
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleStatusChange = async (id: string, newStatus: Status) => {
    try {
      setErrorMsg(null);
      await updateStatus(id, newStatus);
      onStatusUpdate();
    } catch (err: any) {
      if (err.status === 409) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg('Failed to update status');
      }
    }
  };

  const truncate = (str: string) => str.length > 50 ? str.substring(0, 47) + '...' : str;

  return (
    <div className="card">
      <h2>Complaints</h2>
      {errorMsg && <div className="error-text" style={{marginBottom: '1rem'}}>{errorMsg}</div>}
      
      {complaints.length === 0 ? (
        <p>No complaints found.</p>
      ) : (
        <div>
          {complaints.map(c => (
            <div key={c.id} className="complaint-item">
              <div className="complaint-header">
                <strong>{truncate(c.text)}</strong>
                <StatusBadge status={c.status} />
              </div>
              <div style={{ fontSize: '0.875rem', color: '#666', marginBottom: '0.5rem' }}>
                {c.location} | <span className="badge" style={{background: '#eee'}}>{c.category}</span> | <span className="badge" style={{background: '#eee'}}>{c.priority}</span>
              </div>
              
              <select 
                value={c.status} 
                onChange={(e) => handleStatusChange(c.id, e.target.value as Status)}
                className="form-control"
                style={{ width: 'auto', display: 'inline-block', padding: '0.25rem' }}
              >
                <option value="open">Open</option>
                <option value="in_progress">In Progress</option>
                <option value="resolved">Resolved</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ComplaintList;
