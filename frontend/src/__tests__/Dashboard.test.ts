import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import Dashboard from '../pages/Dashboard.svelte';

const mockMembers = [
  { id: '1', firstname: 'Alice', lastname: 'Dupont', invoice_generated: true, email_sent: true },
  { id: '2', firstname: 'Bob', lastname: 'Martin', invoice_generated: true, email_sent: false },
  { id: '3', firstname: 'Charlie', lastname: 'Durand', invoice_generated: false, email_sent: false },
];

const mockSummary = {
  activities: [
    { name: 'Football', count: 15, members: ['Alice Dupont', 'Bob Martin'] },
    { name: 'Tennis', count: 10, members: ['Charlie Durand'] },
    { name: 'Yoga', count: 5, members: ['Diana Prince'] },
  ],
  total: 30,
};

function mockFetchSuccess() {
  globalThis.fetch = vi.fn().mockImplementation((url: string) => {
    if (url.includes('/api/members')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockMembers) });
    }
    if (url.includes('/api/summary')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockSummary) });
    }
    if (url.includes('/api/campaigns/refresh')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ message: 'ok' }) });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  });
}

describe('Dashboard', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mockFetchSuccess();
  });

  it('shows total members count', async () => {
    render(Dashboard);
    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('Total membres')).toBeInTheDocument();
    });
  });

  it('shows invoices generated count', async () => {
    render(Dashboard);
    await waitFor(() => {
      expect(screen.getByText('Factures générées')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
    });
  });

  it('shows emails sent count', async () => {
    render(Dashboard);
    await waitFor(() => {
      expect(screen.getByText('Emails envoyés')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
    });
  });

  it('shows refresh button', async () => {
    render(Dashboard);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /rafraîchir/i })).toBeInTheDocument();
    });
  });

  // Summary integration tests
  it('shows activity breakdown table', async () => {
    render(Dashboard);
    await waitFor(() => {
      expect(screen.getByText('Football')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument();
      expect(screen.getByText('Tennis')).toBeInTheDocument();
      expect(screen.getByText('Yoga')).toBeInTheDocument();
    });
  });

  it('shows total inscriptions count', async () => {
    render(Dashboard);
    await waitFor(() => {
      expect(screen.getByText('Total (inscriptions)')).toBeInTheDocument();
      expect(screen.getByText('30')).toBeInTheDocument();
    });
  });

  it('expands activity to show member names on click', async () => {
    render(Dashboard);
    await waitFor(() => {
      expect(screen.getByText('Football')).toBeInTheDocument();
    });

    expect(screen.queryByText('Alice Dupont')).not.toBeInTheDocument();

    await fireEvent.click(screen.getByText('Football'));

    await waitFor(() => {
      expect(screen.getByText('Alice Dupont')).toBeInTheDocument();
    });
  });
});
