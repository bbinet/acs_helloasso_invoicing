import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import App from '../App.svelte';

describe('Auth guard', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    // Reset hash to dashboard
    window.location.hash = '#/';
  });

  it('redirects to login when checkAuth returns 401', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: () => Promise.resolve({ detail: 'Not authenticated' }),
    });

    render(App);

    await waitFor(() => {
      expect(window.location.hash).toBe('#/login');
    });
  });

  it('shows dashboard when checkAuth succeeds', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/auth/check')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'authenticated' }) });
      }
      if (url.includes('/api/members')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
      if (url.includes('/api/summary')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ activities: [], total: 0 }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });

    render(App);

    await waitFor(() => {
      // Dashboard page renders with stats — check for "Total membres" which is unique to Dashboard
      expect(screen.getByText('Total membres')).toBeInTheDocument();
    });
  });
});
