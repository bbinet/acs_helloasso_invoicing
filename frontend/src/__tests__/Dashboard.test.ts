import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import Dashboard from '../pages/Dashboard.svelte';

const mockMembers = [
  { id: '1', first_name: 'Alice', last_name: 'Dupont', invoice_generated: true, email_sent: true },
  { id: '2', first_name: 'Bob', last_name: 'Martin', invoice_generated: true, email_sent: false },
  { id: '3', first_name: 'Charlie', last_name: 'Durand', invoice_generated: false, email_sent: false },
];

const mockSummary = {
  recent_activity: [
    { date: '2026-03-20', action: 'Invoice generated', member: 'Alice Dupont' },
  ],
};

function mockFetchSuccess() {
  globalThis.fetch = vi.fn().mockImplementation((url: string) => {
    if (url.includes('/api/members')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockMembers),
      });
    }
    if (url.includes('/api/summary')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockSummary),
      });
    }
    if (url.includes('/api/campaigns/refresh')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ message: 'ok' }),
      });
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
});
