import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import ComplaintForm from '../src/components/ComplaintForm';
import * as apiClient from '../src/api/client';

vi.mock('../src/api/client', () => ({
  createComplaint: vi.fn()
}));

describe('ComplaintForm', () => {
  it('validates text length', async () => {
    render(<ComplaintForm />);
    
    const textInput = screen.getByLabelText(/Description/i);
    fireEvent.change(textInput, { target: { value: 'short' } });
    
    const submitBtn = screen.getByRole('button', { name: /Submit/i });
    fireEvent.click(submitBtn);
    
    expect(await screen.findByText('Text must be between 10 and 2000 characters')).toBeInTheDocument();
  });

  it('successful submission shows triage result', async () => {
    (apiClient.createComplaint as any).mockResolvedValue({
      id: '1',
      category: 'roads',
      priority: 'high',
      ai_summary: 'Pothole issue',
      triaged_by: 'ai'
    });

    render(<ComplaintForm />);
    
    fireEvent.change(screen.getByLabelText(/Description/i), { target: { value: 'There is a huge pothole here.' } });
    fireEvent.change(screen.getByLabelText(/Location/i), { target: { value: 'Main St' } });
    
    fireEvent.click(screen.getByRole('button', { name: /Submit/i }));
    
    await waitFor(() => {
      expect(screen.getByText('Triage Result')).toBeInTheDocument();
      expect(screen.getByText('roads')).toBeInTheDocument();
      expect(screen.getByText('high')).toBeInTheDocument();
      expect(screen.getByText('Pothole issue')).toBeInTheDocument();
    });
  });
});
