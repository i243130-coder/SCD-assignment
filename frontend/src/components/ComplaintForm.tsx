import React, { useState } from 'react';
import { createComplaint } from '../api/client';
import { ComplaintResponse } from '../types';

const ComplaintForm: React.FC = () => {
  const [text, setText] = useState('');
  const [location, setLocation] = useState('');
  const [reporterContact, setReporterContact] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ComplaintResponse | null>(null);
  const [validationErrors, setValidationErrors] = useState<{text?: string, location?: string}>({});

  const validate = () => {
    const errs: {text?: string, location?: string} = {};
    if (text.length < 10 || text.length > 2000) {
      errs.text = 'Text must be between 10 and 2000 characters';
    }
    if (location.length < 3 || location.length > 200) {
      errs.location = 'Location must be between 3 and 200 characters';
    }
    setValidationErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await createComplaint({
        text,
        location,
        reporter_contact: reporterContact || null
      });
      setResult(res);
      setText('');
      setLocation('');
      setReporterContact('');
    } catch (err: any) {
      setError(err.message || 'Failed to submit complaint');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Submit Complaint</h2>
      {error && <div className="error-text" style={{marginBottom: '1rem'}}>{error}</div>}
      
      {result && (
        <div className="card" style={{backgroundColor: '#e8f4f8', border: '1px solid #3498db'}}>
          <h3>Triage Result</h3>
          <p><strong>Category:</strong> {result.category}</p>
          <p><strong>Priority:</strong> {result.priority}</p>
          <p><strong>Summary:</strong> {result.ai_summary}</p>
          <p><strong>Triaged By:</strong> {result.triaged_by}</p>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="text">Description</label>
          <textarea
            id="text"
            className="form-control"
            rows={4}
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          {validationErrors.text && <div className="error-text">{validationErrors.text}</div>}
        </div>

        <div className="form-group">
          <label htmlFor="location">Location</label>
          <input
            id="location"
            type="text"
            className="form-control"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />
          {validationErrors.location && <div className="error-text">{validationErrors.location}</div>}
        </div>

        <div className="form-group">
          <label htmlFor="contact">Contact (Optional)</label>
          <input
            id="contact"
            type="text"
            className="form-control"
            value={reporterContact}
            onChange={(e) => setReporterContact(e.target.value)}
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Submitting...' : 'Submit'}
        </button>
      </form>
    </div>
  );
};

export default ComplaintForm;
