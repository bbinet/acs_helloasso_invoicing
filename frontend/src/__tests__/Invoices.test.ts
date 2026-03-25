import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import Members from '../pages/Members.svelte';

const mockMembers = [
  { id: '1', firstname: 'Alice', lastname: 'Dupont', email: 'alice@test.com', company: 'ACME', activities: ['Football'], order_date: '2026-01-15', ea: false, invoice_generated: true, email_sent: false, email_error: false, email_date: null, email_log: null },
  { id: '2', firstname: 'Bob', lastname: 'Martin', email: 'bob@test.com', company: 'Globex', activities: ['Tennis'], order_date: '2026-01-20', ea: true, invoice_generated: false, email_sent: false, email_error: false, email_date: null, email_log: null },
];

function mockFetchDefault() {
  globalThis.fetch = vi.fn().mockImplementation((url: string) => {
    if (url.includes('/api/members')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockMembers) });
    }
    if (url.includes('/api/invoices/batch') && !url.includes('status')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ job_id: 'job-123' }) });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  });
}

describe('Members page - Invoice & Email features', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mockFetchDefault();
  });

  it('renders member list with invoice status columns', async () => {
    render(Members);

    await waitFor(() => {
      expect(screen.getByText('Dupont')).toBeInTheDocument();
      expect(screen.getByText('Martin')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /^Facture/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Envoi/ })).toBeInTheDocument();
  });

  it('batch generate button calls batch API', async () => {
    render(Members);

    await waitFor(() => {
      expect(screen.getByText('Dupont')).toBeInTheDocument();
    });

    const batchBtn = screen.getByRole('button', { name: /générer les factures/i });
    await fireEvent.click(batchBtn);

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/invoices/batch'),
        expect.objectContaining({ method: 'POST' }),
      );
    });
  });

  it('shows invoice dropdown with preview when clicking ✓ badge', async () => {
    render(Members);

    await waitFor(() => {
      expect(screen.getByText('Dupont')).toBeInTheDocument();
    });

    // Alice has invoice_generated=true, click her ✓ badge
    const badges = screen.getAllByText('✓');
    await fireEvent.click(badges[0]);

    await waitFor(() => {
      expect(screen.getByText(/aperçu/i)).toBeInTheDocument();
      expect(screen.getByText(/télécharger/i)).toBeInTheDocument();
    });
  });

  it('shows dash badge for members without invoice', async () => {
    render(Members);

    await waitFor(() => {
      expect(screen.getByText('Martin')).toBeInTheDocument();
    });

    // Bob has invoice_generated=false — should show — badge (not ✗)
    const dashBadges = screen.getAllByText('—');
    expect(dashBadges.length).toBeGreaterThanOrEqual(1);
  });
});
