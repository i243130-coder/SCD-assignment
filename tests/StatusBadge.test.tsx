import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import StatusBadge from '../src/components/StatusBadge';

describe('StatusBadge', () => {
  it('renders correct color for each status', () => {
    const { unmount } = render(<StatusBadge status="open" />);
    expect(screen.getByTestId('status-badge')).toHaveStyle({ backgroundColor: '#2ecc71' });
    unmount();
    
    render(<StatusBadge status="rejected" />);
    expect(screen.getByTestId('status-badge')).toHaveStyle({ backgroundColor: '#e74c3c' });
  });
});
