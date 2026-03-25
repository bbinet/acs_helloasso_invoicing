import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, within, waitFor } from '@testing-library/svelte';
import MemberTable from '../components/MemberTable.svelte';

const mockData = Array.from({ length: 25 }, (_, i) => ({
  id: String(i + 1),
  last_name: `Nom${String(i + 1).padStart(2, '0')}`,
  first_name: `Prenom${String(i + 1).padStart(2, '0')}`,
  company: i % 2 === 0 ? 'ACME' : 'Globex',
  email: `user${i + 1}@test.com`,
  activities: i % 3 === 0 ? 'Football' : i % 3 === 1 ? 'Tennis' : 'Yoga',
  date: `2026-01-${String(i + 1).padStart(2, '0')}`,
  ea: i % 2 === 0,
  invoice_generated: i < 10,
  email_sent: i < 5,
}));

describe('MemberTable', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders rows from data prop', () => {
    render(MemberTable, { props: { data: mockData.slice(0, 3) } });

    expect(screen.getByText('Nom01')).toBeInTheDocument();
    expect(screen.getByText('Nom02')).toBeInTheDocument();
    expect(screen.getByText('Nom03')).toBeInTheDocument();
  });

  it('sorts by column when header clicked', async () => {
    render(MemberTable, { props: { data: mockData.slice(0, 5) } });

    // Click "Nom" header to sort - use exact match to avoid matching "Prénom"
    const nomHeader = screen.getByRole('button', { name: /^Nom/ });
    // Default is already ascending on last_name, so first click toggles to descending
    await fireEvent.click(nomHeader);

    const rows = screen.getAllByRole('row');
    // First row is header, second should be Nom05 (descending)
    const firstDataRow = rows[1];
    expect(within(firstDataRow).getByText('Nom05')).toBeInTheDocument();
  });

  it('filters by search text input', async () => {
    render(MemberTable, { props: { data: mockData.slice(0, 5) } });

    const searchInput = screen.getByPlaceholderText(/rechercher/i);
    await fireEvent.input(searchInput, { target: { value: 'Nom03' } });

    expect(screen.getByText('Nom03')).toBeInTheDocument();
    expect(screen.queryByText('Nom01')).not.toBeInTheDocument();
  });

  it('filters by activity dropdown', async () => {
    render(MemberTable, { props: { data: mockData.slice(0, 6) } });

    const select = screen.getByRole('combobox');
    await fireEvent.change(select, { target: { value: 'Football' } });

    // Football: indices 0, 3 => Nom01, Nom04
    expect(screen.getByText('Nom01')).toBeInTheDocument();
    expect(screen.getByText('Nom04')).toBeInTheDocument();
    expect(screen.queryByText('Nom02')).not.toBeInTheDocument();
  });

  it('paginates with 20 per page and shows next/prev', async () => {
    render(MemberTable, { props: { data: mockData } });

    // First page: 20 items, so Nom21 should NOT be visible
    expect(screen.getByText('Nom01')).toBeInTheDocument();
    expect(screen.queryByText('Nom21')).not.toBeInTheDocument();

    // Click next page
    const nextBtn = screen.getByRole('button', { name: /suivant/i });
    await fireEvent.click(nextBtn);

    // Now page 2: Nom21-Nom25 visible, Nom01 not
    expect(screen.getByText('Nom21')).toBeInTheDocument();
    expect(screen.queryByText('Nom01')).not.toBeInTheDocument();
  });

  it('shows status badges for invoice and email', () => {
    render(MemberTable, { props: { data: mockData.slice(0, 2) } });

    // Member 0 has invoice_generated=true, email_sent=true => two success badges
    // Member 1 has invoice_generated=true, email_sent=false => one success, one error
    const badges = screen.getAllByText('✓');
    expect(badges.length).toBeGreaterThanOrEqual(2);

    const errorBadges = screen.getAllByText('✗');
    expect(errorBadges.length).toBeGreaterThanOrEqual(1);
  });

  it('action buttons fire event callbacks', async () => {
    const onGenerateInvoice = vi.fn();
    const onSendEmail = vi.fn();
    const onDownload = vi.fn();

    render(MemberTable, {
      props: {
        data: mockData.slice(0, 1),
        onGenerateInvoice,
        onSendEmail,
        onDownload,
      },
    });

    const generateBtn = screen.getByTitle('Générer facture');
    const sendBtn = screen.getByTitle('Envoyer email');
    const downloadBtn = screen.getByTitle('Télécharger PDF');

    await fireEvent.click(generateBtn);
    expect(onGenerateInvoice).toHaveBeenCalledWith('1');

    await fireEvent.click(sendBtn);
    expect(onSendEmail).toHaveBeenCalledWith('1');

    await fireEvent.click(downloadBtn);
    expect(onDownload).toHaveBeenCalledWith('1');
  });
});
