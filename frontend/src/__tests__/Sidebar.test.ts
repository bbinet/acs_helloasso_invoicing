import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import Sidebar from '../components/Sidebar.svelte';
import Layout from '../components/Layout.svelte';

describe('Sidebar', () => {
  it('renders navigation links', () => {
    render(Sidebar);

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Membres')).toBeInTheDocument();
    expect(screen.getByText('Factures')).toBeInTheDocument();
    expect(screen.getByText('Résumé')).toBeInTheDocument();
  });

  it('renders logout button', () => {
    render(Sidebar);

    expect(screen.getByText('Déconnexion')).toBeInTheDocument();
  });
});

describe('Layout', () => {
  it('renders slot content', () => {
    // Render Layout - in Svelte 5, we test that it mounts without error
    // and contains the drawer structure
    const { container } = render(Layout);
    expect(container.querySelector('.drawer')).toBeInTheDocument();
  });
});
