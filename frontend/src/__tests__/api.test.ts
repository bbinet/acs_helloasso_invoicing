import { describe, it, expect, vi, beforeEach } from 'vitest';

// We'll import the module under test after writing the implementation
// For now, define what we expect from the API client

describe('apiFetch', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('calls fetch with correct URL and credentials: include', async () => {
    const mockResponse = { ok: true, json: () => Promise.resolve({ status: 'ok' }) };
    globalThis.fetch = vi.fn().mockResolvedValue(mockResponse);

    const { apiFetch } = await import('../lib/api');
    await apiFetch('/health');

    expect(globalThis.fetch).toHaveBeenCalledWith('/api/health', expect.objectContaining({
      credentials: 'include',
    }));
  });

  it('parses JSON response', async () => {
    const data = { status: 'ok', version: '1.0' };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(data),
    });

    const { apiFetch } = await import('../lib/api');
    const result = await apiFetch('/health');
    expect(result).toEqual(data);
  });

  it('throws on non-ok response', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.resolve({ detail: 'Server error' }),
    });

    const { apiFetch } = await import('../lib/api');
    await expect(apiFetch('/health')).rejects.toThrow();
  });
});

describe('login', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('POSTs to /api/auth/login with JSON body', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ message: 'ok' }),
    });

    const { login } = await import('../lib/api');
    await login('secret123');

    expect(globalThis.fetch).toHaveBeenCalledWith('/api/auth/login', expect.objectContaining({
      method: 'POST',
      credentials: 'include',
      headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ password: 'secret123' }),
    }));
  });
});

describe('getMembers', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('GETs /api/members', async () => {
    const members = [{ id: 1, name: 'Alice' }];
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(members),
    });

    const { getMembers } = await import('../lib/api');
    const result = await getMembers();

    expect(globalThis.fetch).toHaveBeenCalledWith('/api/members', expect.objectContaining({
      credentials: 'include',
    }));
    expect(result).toEqual(members);
  });

  it('adds query params when provided', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    });

    const { getMembers } = await import('../lib/api');
    await getMembers({ activity: 'foot' });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/members?activity=foot'),
      expect.any(Object),
    );
  });
});
