import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ComplaintList from '../src/components/ComplaintList';

describe('ComplaintList', () => {
  const mockComplaints: any[] = [
    {
      id: '1',
      text: 'Long complaint text here to test rendering',
      location: '123 Main St',
      category: 'water',
      priority: 'high',
      status: 'open'
    }
  ];

  it('renders complaint items', () => {
    render(<ComplaintList complaints={mockComplaints} onStatusUpdate={vi.fn()} />);
    expect(screen.getByText(/Long complaint text here/i)).toBeInTheDocument();
    expect(screen.getByText(/123 Main St/)).toBeInTheDocument();
    expect(screen.getByText(/water/)).toBeInTheDocument();
  });
});
