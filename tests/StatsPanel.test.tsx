import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import StatsPanel from '../src/components/StatsPanel';
import * as apiClient from '../src/api/client';

vi.mock('../src/api/client', () => ({
  getStats: vi.fn()
}));

describe('StatsPanel', () => {
  it('renders category stats', async () => {
    (apiClient.getStats as any).mockResolvedValue({
      data: {
        categories: [{ category: 'roads', count: 5 }],
        priorities: [{ priority: 'high', count: 5 }],
        total: 5
      },
      cacheStatus: 'HIT'
    });

    render(<StatsPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('roads')).toBeInTheDocument();
      expect(screen.getByText('Cache: HIT')).toBeInTheDocument();
    });
  });
});
