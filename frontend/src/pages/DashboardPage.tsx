import React, { useEffect, useState, useCallback } from 'react';
import { listComplaints } from '../api/client';
import { ComplaintResponse, Category, Priority, Status } from '../types';
import ComplaintList from '../components/ComplaintList';
import StatsPanel from '../components/StatsPanel';

const DashboardPage: React.FC = () => {
  const [complaints, setComplaints] = useState<ComplaintResponse[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  
  const [category, setCategory] = useState<string>('');
  const [priority, setPriority] = useState<string>('');
  const [status, setStatus] = useState<string>('');
  
  const [loading, setLoading] = useState(false);

  const fetchComplaints = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listComplaints(page, 10, category, priority, status);
      setComplaints(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [page, category, priority, status]);

  useEffect(() => {
    fetchComplaints();
  }, [fetchComplaints]);

  return (
    <div>
      <h1 style={{ marginBottom: '2rem' }}>Dashboard</h1>
      
      <div className="dashboard-layout">
        <div className="complaint-list">
          <div className="card filter-bar">
            <select className="form-control" value={category} onChange={e => { setCategory(e.target.value); setPage(1); }}>
              <option value="">All Categories</option>
              <option value="water">Water</option>
              <option value="electricity">Electricity</option>
              <option value="sanitation">Sanitation</option>
              <option value="roads">Roads</option>
              <option value="streetlights">Streetlights</option>
              <option value="other">Other</option>
            </select>
            
            <select className="form-control" value={priority} onChange={e => { setPriority(e.target.value); setPage(1); }}>
              <option value="">All Priorities</option>
              <option value="high">High</option>
              <option value="normal">Normal</option>
              <option value="low">Low</option>
            </select>

            <select className="form-control" value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}>
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>

          {loading ? <p>Loading...</p> : (
            <>
              <ComplaintList complaints={complaints} onStatusUpdate={fetchComplaints} />
              
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1rem' }}>
                <button 
                  className="btn" 
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </button>
                <span>Page {page}</span>
                <button 
                  className="btn" 
                  onClick={() => setPage(p => p + 1)}
                  disabled={page * 10 >= total}
                >
                  Next
                </button>
              </div>
            </>
          )}
        </div>
        
        <StatsPanel />
      </div>
    </div>
  );
};

export default DashboardPage;
