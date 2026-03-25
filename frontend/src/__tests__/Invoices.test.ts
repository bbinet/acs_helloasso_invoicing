import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import Invoices from '../pages/Invoices.svelte';

const mockMembers = [
  { id: '1', first_name: 'Alice', last_name: 'Dupont', email: 'alice@test.com', invoice_generated: true, email_sent: false },
  { id: '2', first_name: 'Bob', last_name: 'Martin', email: 'bob@test.com', invoice_generated: false, email_sent: true },
];

function mockFetchDefault() {
  globalThis.fetch = vi.fn().mockImplementation((url: string) => {
    if (url.includes('/api/members')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockMembers),
      });
    }
    if (url.includes('/api/invoices/batch') && !url.includes('status')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ job_id: 'job-123' }),
      });
    }
    if (url.includes('/api/invoices/batch/job-123/status')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: 'done', completed: 2, total: 2, errors: [] }),
      });
    }
    if (url.includes('/api/emails/batch') && !url.includes('status')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ job_id: 'job-456' }),
      });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  });
}

describe('Invoices', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.useFakeTimers();
    mockFetchDefault();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders member list with status columns', async () => {
    vi.useRealTimers();
    render(Invoices);

    await waitFor(() => {
      expect(screen.getByText('Dupont')).toBeInTheDocument();
      expect(screen.getByText('Martin')).toBeInTheDocument();
    });

    // Check table headers include Facture and Email columns
    expect(screen.getByText('Facture')).toBeInTheDocument();
    expect(screen.getByText('Email')).toBeInTheDocument();
  });

  it('batch generate button calls batch API', async () => {
    vi.useRealTimers();
    render(Invoices);

    await waitFor(() => {
      expect(screen.getByText('Dupont')).toBeInTheDocument();
    });

    const batchBtn = screen.getByRole('button', { name: /générer toutes les factures/i });
    await fireEvent.click(batchBtn);

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/invoices/batch',
        expect.objectContaining({ method: 'POST' }),
      );
    });
  });

  it('BatchProgress shows progress bar with completed/total text', async () => {
    // Mock a running job
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/members')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockMembers),
        });
      }
      if (url.includes('/api/invoices/batch') && !url.includes('status')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ job_id: 'job-123' }),
        });
      }
      if (url.includes('/api/invoices/batch/job-123/status')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'running', completed: 1, total: 2, errors: [] }),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });

    render(Invoices);

    await vi.advanceTimersByTimeAsync(0);
    await waitFor(() => {
      expect(screen.getByText('Dupont')).toBeInTheDocument();
    });

    const batchBtn = screen.getByRole('button', { name: /générer toutes les factures/i });
    await fireEvent.click(batchBtn);

    // Advance timer to trigger the first poll
    await vi.advanceTimersByTimeAsync(2000);

    await waitFor(() => {
      expect(screen.getByText(/1 \/ 2/)).toBeInTheDocument();
    });

    // Check progress bar exists
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('BatchProgress shows Termine when status is done', async () => {
    render(Invoices);

    await vi.advanceTimersByTimeAsync(0);
    await waitFor(() => {
      expect(screen.getByText('Dupont')).toBeInTheDocument();
    });

    const batchBtn = screen.getByRole('button', { name: /générer toutes les factures/i });
    await fireEvent.click(batchBtn);

    // Advance timer to trigger poll - default mock returns done
    await vi.advanceTimersByTimeAsync(2000);

    await waitFor(() => {
      expect(screen.getByText(/termin/i)).toBeInTheDocument();
    });
  });

  it('InvoicePreview modal renders with iframe', async () => {
    vi.useRealTimers();
    render(Invoices);

    await waitFor(() => {
      expect(screen.getByText('Dupont')).toBeInTheDocument();
    });

    // Click preview button for first member
    const previewBtns = screen.getAllByTitle(/aperçu/i);
    await fireEvent.click(previewBtns[0]);

    await waitFor(() => {
      const iframe = document.querySelector('iframe');
      expect(iframe).toBeTruthy();
      expect(iframe?.getAttribute('src')).toContain('/api/invoices/1/preview');
    });
  });

  it('per-member download button exists', async () => {
    vi.useRealTimers();
    render(Invoices);

    await waitFor(() => {
      expect(screen.getByText('Dupont')).toBeInTheDocument();
    });

    const downloadBtns = screen.getAllByTitle(/télécharger/i);
    expect(downloadBtns.length).toBeGreaterThanOrEqual(1);
  });
});
