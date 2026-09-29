import React, { useEffect, useState } from 'react';
import { getStats } from '../api/client';
import { StatsResponse } from '../types';

const StatsPanel: React.FC = () => {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [cacheStatus, setCacheStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const { data, cacheStatus } = await getStats();
        setStats(data);
        setCacheStatus(cacheStatus);
      } catch (err: any) {
        setError(err.message || 'Failed to load stats');
      }
    };
    fetchStats();
  }, []);

  if (error) return <div className="card"><div className="error-text">{error}</div></div>;
  if (!stats) return <div className="card">Loading stats...</div>;

  return (
    <div className="card stats-panel">
      <h2>Statistics</h2>
      {cacheStatus && (
        <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: '1rem' }}>
          Cache: {cacheStatus}
        </div>
      )}
      
      <div style={{ marginBottom: '1.5rem' }}>
        <h3>Categories</h3>
        {stats.categories.map(c => (
          <div key={c.category} className="stat-row">
            <span>{c.category}</span>
            <strong>{c.count}</strong>
          </div>
        ))}
      </div>

      <div>
        <h3>Priorities</h3>
        {stats.priorities.map(p => (
          <div key={p.priority} className="stat-row">
            <span>{p.priority}</span>
            <strong>{p.count}</strong>
          </div>
        ))}
      </div>
      
      <div className="stat-row" style={{ marginTop: '1rem', background: '#e8f4f8' }}>
        <span>Total Complaints</span>
        <strong>{stats.total}</strong>
      </div>
    </div>
  );
};

export default StatsPanel;
