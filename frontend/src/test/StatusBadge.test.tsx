import { describe, expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusBadge } from '../app/components/shared/StatusBadge';

describe('StatusBadge', () => {
  test('renders a known MediQueue workflow status', () => {
    render(<StatusBadge status="Pending Approval" />);
    expect(screen.getByText('Pending Approval')).toBeInTheDocument();
  });

  test('still renders an unknown status using the fallback style', () => {
    render(<StatusBadge status="Custom Test Status" />);
    expect(screen.getByText('Custom Test Status')).toBeInTheDocument();
  });
});
