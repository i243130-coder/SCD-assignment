import React from 'react';
import ComplaintForm from '../components/ComplaintForm';

const SubmitPage: React.FC = () => {
  return (
    <div>
      <h1 style={{ marginBottom: '0.5rem' }}>Report an Issue</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Help us improve the city by reporting municipal issues like potholes, broken streetlights, or sanitation problems.
      </p>
      <ComplaintForm />
    </div>
  );
};

export default SubmitPage;
