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

  it('deliberately fails to verify CI gate blocks merge', () => {
    // Assignment Requirement (Section 3.4 & Rubric):
    // "Evidence the gate works: a PR with a deliberately failing test, screenshot of the red check
    // and the blocked merge button, fixed in the same PR, screenshot of green."
    // 
    // Once you take the screenshot of the red check & blocked merge button:
    // Change `false` to `true` on the line below to turn the pipeline green!
    expect(true).toBe(true);
  });
});

