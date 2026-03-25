import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import Login from '../pages/Login.svelte';

// Mock svelte-spa-router
vi.mock('svelte-spa-router', () => ({
  push: vi.fn(),
  default: {},
}));

describe('Login', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders password input and submit button', () => {
    render(Login);

    expect(screen.getByPlaceholderText('Mot de passe')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /connexion/i })).toBeInTheDocument();
  });

  it('calls login API on form submit with entered password', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ message: 'ok' }),
    });

    render(Login);

    const input = screen.getByPlaceholderText('Mot de passe');
    const button = screen.getByRole('button', { name: /connexion/i });

    await fireEvent.input(input, { target: { value: 'mysecret' } });
    await fireEvent.click(button);

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/auth/login',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ password: 'mysecret' }),
        }),
      );
    });
  });

  it('shows error message when API returns 401', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: () => Promise.resolve({ detail: 'Mot de passe incorrect' }),
    });

    render(Login);

    const input = screen.getByPlaceholderText('Mot de passe');
    const button = screen.getByRole('button', { name: /connexion/i });

    await fireEvent.input(input, { target: { value: 'wrong' } });
    await fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText('Mot de passe incorrect')).toBeInTheDocument();
    });
  });
});
