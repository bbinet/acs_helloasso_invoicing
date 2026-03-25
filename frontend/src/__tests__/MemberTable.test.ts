import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import MemberTable from '../components/MemberTable.svelte';

const mockData = Array.from({ length: 25 }, (_, i) => ({
  id: String(i + 1),
  lastname: `Nom${String(i + 1).padStart(2, '0')}`,
  firstname: `Prenom${String(i + 1).padStart(2, '0')}`,
  company: i % 2 === 0 ? 'ACME' : 'Globex',
  email: `user${i + 1}@test.com`,
  activities: i % 3 === 0 ? ['Football'] : i % 3 === 1 ? ['Tennis'] : ['Yoga'],
  order_date: `2026-01-${String(i + 1).padStart(2, '0')}`,
  ea: i % 2 === 0,
  invoice_generated: i < 10,
  email_sent: i < 5,
  email_error: false,
  email_date: i < 5 ? '2026-03-20T10:00:00' : null,
  email_log: null,
}));

beforeEach(() => {
  vi.restoreAllMocks();
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({}),
  });
});

describe('MemberTable', () => {
  it('renders rows from data prop', () => {
    render(MemberTable, { props: { data: mockData.slice(0, 3) } });

    expect(screen.getByText('Nom01')).toBeInTheDocument();
    expect(screen.getByText('Nom02')).toBeInTheDocument();
    expect(screen.getByText('Nom03')).toBeInTheDocument();
  });

  it('does not render # index column', () => {
    render(MemberTable, { props: { data: mockData.slice(0, 3) } });

    // No # column header
    const headers = screen.getAllByRole('columnheader');
    const headerTexts = headers.map(h => h.textContent?.trim());
    expect(headerTexts).not.toContain('#');
  });

  it('sorts by column when header clicked', async () => {
    render(MemberTable, { props: { data: mockData.slice(0, 5) } });

    const nomHeader = screen.getByRole('button', { name: /^Nom/ });
    await fireEvent.click(nomHeader);

    const rows = screen.getAllByRole('row');
    const firstDataRow = rows[1];
    expect(firstDataRow.textContent).toContain('Nom05');
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

    expect(screen.getByText('Nom01')).toBeInTheDocument();
    expect(screen.getByText('Nom04')).toBeInTheDocument();
    expect(screen.queryByText('Nom02')).not.toBeInTheDocument();
  });

  it('paginates with 20 per page', async () => {
    render(MemberTable, { props: { data: mockData } });

    expect(screen.getByText('Nom01')).toBeInTheDocument();
    expect(screen.queryByText('Nom21')).not.toBeInTheDocument();

    const nextBtn = screen.getByRole('button', { name: /suivant/i });
    await fireEvent.click(nextBtn);

    expect(screen.getByText('Nom21')).toBeInTheDocument();
    expect(screen.queryByText('Nom01')).not.toBeInTheDocument();
  });

  it('shows status badges for invoice and email', () => {
    const mixedData = [
      { ...mockData[0], invoice_generated: true, email_sent: true, email_date: '2026-03-25' },
      { ...mockData[1], invoice_generated: false, email_sent: false },
    ];
    render(MemberTable, { props: { data: mixedData } });

    const successBadges = screen.getAllByText('✓');
    expect(successBadges.length).toBeGreaterThanOrEqual(2);

    // Not-generated invoice shows — (dash)
    const dashBadges = screen.getAllByText('—');
    expect(dashBadges.length).toBeGreaterThanOrEqual(1);
  });

  it('invoice and email status are clickable buttons', () => {
    const data = [
      { ...mockData[0], invoice_generated: true, email_sent: false },
    ];
    render(MemberTable, { props: { data } });

    // Status buttons use btn class
    const buttons = screen.getAllByRole('button');
    const statusButtons = buttons.filter(b =>
      b.classList.contains('btn-success') || b.classList.contains('btn-ghost')
    );
    expect(statusButtons.length).toBeGreaterThanOrEqual(2);
  });

  it('batch buttons show count from filtered data', () => {
    const onBatchGenerate = vi.fn();
    const data = [
      { ...mockData[0], invoice_generated: true },
      { ...mockData[1], invoice_generated: false },
      { ...mockData[2], invoice_generated: false },
    ];
    render(MemberTable, { props: { data, onBatchGenerate } });

    // Button should show count of not-yet-generated
    const btn = screen.getByRole('button', { name: /générer les factures/i });
    expect(btn.textContent).toContain('2');
  });
});
