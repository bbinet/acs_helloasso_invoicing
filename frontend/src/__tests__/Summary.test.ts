import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import Summary from '../pages/Summary.svelte';

const mockSummary = {
  activities: [
    { name: 'Football', count: 15, members: ['Alice Dupont', 'Bob Martin', 'Charlie Durand'] },
    { name: 'Tennis', count: 10, members: ['Diana Prince', 'Eve Adams'] },
    { name: 'Yoga', count: 5, members: ['Frank Castle'] },
  ],
  total: 30,
};

function mockFetchSuccess() {
  globalThis.fetch = vi.fn().mockImplementation((url: string) => {
    if (url.includes('/api/summary')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockSummary),
      });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  });
}

describe('Summary', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mockFetchSuccess();
  });

  it('renders activities with member counts', async () => {
    render(Summary);

    await waitFor(() => {
      expect(screen.getByText('Football')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument();
      expect(screen.getByText('Tennis')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('Yoga')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
    });
  });

  it('shows total at bottom', async () => {
    render(Summary);

    await waitFor(() => {
      expect(screen.getByText('Total')).toBeInTheDocument();
      expect(screen.getByText('30')).toBeInTheDocument();
    });
  });

  it('expands to show member names on click', async () => {
    render(Summary);

    await waitFor(() => {
      expect(screen.getByText('Football')).toBeInTheDocument();
    });

    // Members should not be visible initially
    expect(screen.queryByText('Alice Dupont')).not.toBeInTheDocument();

    // Click on Football row to expand
    const footballRow = screen.getByText('Football');
    await fireEvent.click(footballRow);

    await waitFor(() => {
      expect(screen.getByText('Alice Dupont')).toBeInTheDocument();
      expect(screen.getByText('Bob Martin')).toBeInTheDocument();
    });
  });
});
