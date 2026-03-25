import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import Navbar from '../components/Navbar.svelte';
import Layout from '../components/Layout.svelte';

describe('Navbar', () => {
  it('renders navigation tabs on the left', () => {
    render(Navbar);

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Membres')).toBeInTheDocument();
  });

  it('renders logout button on the right', () => {
    render(Navbar);

    expect(screen.getByText('Déconnexion')).toBeInTheDocument();
  });

  it('tabs and logout are in separate flex containers', () => {
    const { container } = render(Navbar);

    // flex-1 contains tabs, flex-none contains logout
    const flex1 = container.querySelector('.flex-1');
    const flexNone = container.querySelector('.flex-none');
    expect(flex1?.textContent).toContain('Dashboard');
    expect(flexNone?.textContent).toContain('Déconnexion');
  });
});

describe('Layout', () => {
  it('renders navbar', () => {
    const { container } = render(Layout);
    expect(container.querySelector('.navbar')).toBeInTheDocument();
  });
});
