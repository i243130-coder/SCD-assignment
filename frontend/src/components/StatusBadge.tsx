import React from 'react';
import { Status } from '../types';

interface Props {
  status: Status | string;
}

const StatusBadge: React.FC<Props> = ({ status }) => {
  let color = '#7f8c8d'; // gray
  let bgColor = '#f8f9fa';

  switch (status) {
    case 'open':
      color = '#fff';
      bgColor = '#2ecc71'; // green
      break;
    case 'in_progress':
      color = '#fff';
      bgColor = '#3498db'; // blue
      break;
    case 'resolved':
      color = '#fff';
      bgColor = '#95a5a6'; // gray
      break;
    case 'rejected':
      color = '#fff';
      bgColor = '#e74c3c'; // red
      break;
  }

  return (
    <span data-testid="status-badge" className="badge" style={{ backgroundColor: bgColor, color }}>
      {status.replace('_', ' ')}
    </span>
  );
};

export default StatusBadge;
