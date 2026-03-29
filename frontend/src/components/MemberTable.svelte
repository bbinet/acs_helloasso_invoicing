<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import BatchProgress from './BatchProgress.svelte';
  import InvoicePreview from './InvoicePreview.svelte';
  import Icon from '../lib/Icon.svelte';

  let {
    data = [],
    loadingInvoiceId = null,
    loadingEmailId = null,
    onGenerateInvoice,
    onSendEmail,
    onDownload,
    onDeleteInvoice,
    onRegenerateInvoice,
    onBatchGenerate,
    onBatchSend,
    onBatchComplete,
  }: {
    data: any[];
    loadingInvoiceId?: string | null;
    loadingEmailId?: string | null;
    onGenerateInvoice?: (id: string) => void;
    onSendEmail?: (id: string) => void;
    onDownload?: (id: string) => void;
    onDeleteInvoice?: (id: string) => void;
    onRegenerateInvoice?: (id: string) => void;
    onBatchGenerate?: (memberIds: string[]) => Promise<{job_id: string}>;
    onBatchSend?: (memberIds: string[]) => Promise<{job_id: string}>;
    onBatchComplete?: () => void;
  } = $props();

  // Table state
  let sortColumn = $state('lastname');
  let sortDirection = $state<'asc' | 'desc'>('asc');
  let searchText = $state('');
  let activityFilter = $state('');
  let currentPage = $state(1);

  // Batch state
  let batchJobId = $state<string | null>(null);
  let batchType = $state<'invoices' | 'emails'>('invoices');
  let showBatchProgress = $state(false);

  // Preview state
  let previewMemberId = $state<number | null>(null);
  let showPreview = $state(false);

  // Dropdown state
  let openDropdown = $state<string | null>(null);
  let dropdownPos = $state({ x: 0, y: 0 });

  const PAGE_SIZE = 20;
  const DROPDOWN_WIDTH = 192;

  // Derived data
  let uniqueActivities = $derived(
    [...new Set(data.flatMap((m) => m.activities || []))].sort()
  );

  let filteredData = $derived.by(() => {
    let result = data;
    if (searchText) {
      const term = searchText.toLowerCase();
      result = result.filter(
        (m) =>
          m.lastname?.toLowerCase().includes(term) ||
          m.firstname?.toLowerCase().includes(term) ||
          m.email?.toLowerCase().includes(term) ||
          m.company?.toLowerCase().includes(term)
      );
    }
    if (activityFilter) {
      result = result.filter((m) =>
        (m.activities || []).some((a: string) => a === activityFilter)
      );
    }
    return result;
  });

  let sortedData = $derived.by(() => {
    const col = sortColumn;
    const dir = sortDirection === 'asc' ? 1 : -1;
    return [...filteredData].sort((a, b) => {
      let va = a[col] ?? '';
      let vb = b[col] ?? '';
      if (Array.isArray(va)) va = va.join(', ');
      if (Array.isArray(vb)) vb = vb.join(', ');
      if (typeof va === 'boolean') va = va ? 1 : 0;
      if (typeof vb === 'boolean') vb = vb ? 1 : 0;
      if (va < vb) return -1 * dir;
      if (va > vb) return 1 * dir;
      return 0;
    });
  });

  let filteredIds = $derived(sortedData.map(m => String(m.id)));
  let totalPages = $derived(Math.max(1, Math.ceil(sortedData.length / PAGE_SIZE)));
  let paginatedData = $derived(
    sortedData.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)
  );

  // Close dropdown on click outside
  onMount(() => document.addEventListener('click', closeDropdowns));
  onDestroy(() => document.removeEventListener('click', closeDropdowns));

  // Handlers
  function toggleSort(column: string) {
    if (sortColumn === column) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      sortColumn = column;
      sortDirection = 'asc';
    }
  }

  function sortIndicator(column: string) {
    if (sortColumn !== column) return '';
    return sortDirection === 'asc' ? ' ↑' : ' ↓';
  }

  function handleSearch(e: Event) {
    searchText = (e.target as HTMLInputElement).value;
    currentPage = 1;
  }

  function handleActivityChange(e: Event) {
    activityFilter = (e.target as HTMLSelectElement).value;
    currentPage = 1;
  }

  function toggleDropdown(key: string, e: MouseEvent) {
    if (openDropdown === key) {
      openDropdown = null;
    } else {
      const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
      const x = Math.min(rect.left, window.innerWidth - DROPDOWN_WIDTH - 8);
      dropdownPos = { x, y: rect.top };
      openDropdown = key;
    }
  }

  function closeDropdowns() {
    openDropdown = null;
  }

  async function handleBatchGenerate() {
    if (!onBatchGenerate) return;
    try {
      const result = await onBatchGenerate(filteredIds);
      batchJobId = result.job_id;
      batchType = 'invoices';
      showBatchProgress = true;
    } catch { /* handled by parent */ }
  }

  async function handleBatchSend() {
    if (!onBatchSend) return;
    try {
      const result = await onBatchSend(filteredIds);
      batchJobId = result.job_id;
      batchType = 'emails';
      showBatchProgress = true;
    } catch { /* handled by parent */ }
  }

  function handleBatchDone() {
    showBatchProgress = false;
    onBatchComplete?.();
  }

  function handlePreview(memberId: number) {
    previewMemberId = memberId;
    showPreview = true;
    closeDropdowns();
  }

  function handleClosePreview() {
    showPreview = false;
    previewMemberId = null;
  }

  function exportCSV() {
    const headers = ['HelloAssoID', 'Inscription', 'Nom', 'Prenom', 'Entreprise', 'Email', 'EA', 'Activites', 'Facture', 'Date facture', 'Email envoye', 'Date envoi'];
    const rows = sortedData.map((m) => [
      m.id,
      m.order_date || '',
      m.lastname,
      m.firstname,
      m.company || '',
      m.email,
      m.ea ? 'Oui' : 'Non',
      (m.activities || []).join(' - '),
      m.invoice_generated ? 'Oui' : 'Non',
      m.invoice_date || '',
      m.email_sent ? 'Oui' : m.email_error ? 'Erreur' : 'Non',
      m.email_date || '',
    ]);

    const csvContent = [headers, ...rows]
      .map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
      .join('\n');

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'membres.csv';
    a.click();
    URL.revokeObjectURL(url);
  }
</script>

<div class="space-y-4">
  <!-- Batch actions -->
  <div class="flex gap-2 flex-wrap">
    {#if onBatchGenerate}
      <button class="btn btn-outline btn-sm" onclick={handleBatchGenerate}>
        <Icon name="document" />
        <span class="hidden sm:inline">Générer les factures</span>
        <span class="sm:hidden">Factures</span>
        ({sortedData.filter(m => !m.invoice_generated).length})
      </button>
    {/if}
    {#if onBatchSend}
      <button class="btn btn-outline btn-sm" onclick={handleBatchSend}>
        <Icon name="mail" />
        <span class="hidden sm:inline">Envoyer les emails</span>
        <span class="sm:hidden">Emails</span>
        ({sortedData.filter(m => m.invoice_generated && !m.email_sent).length})
      </button>
    {/if}
    <button class="btn btn-outline btn-sm" onclick={exportCSV}>
      <Icon name="export" />
      <span class="hidden sm:inline">Exporter CSV</span>
      <span class="sm:hidden">CSV</span>
      ({sortedData.length})
    </button>
  </div>

  <!-- Batch progress -->
  {#if showBatchProgress && batchJobId}
    <BatchProgress
      jobId={batchJobId}
      type={batchType}
      onComplete={handleBatchDone}
    />
  {/if}

  <!-- Filters -->
  <div class="flex flex-wrap gap-4 items-center">
    <input
      type="text"
      placeholder="Rechercher (nom, email, entreprise)..."
      class="input input-bordered w-64"
      value={searchText}
      oninput={handleSearch}
    />
    <select class="select select-bordered" value={activityFilter} onchange={handleActivityChange}>
      <option value="">Toutes les activités</option>
      {#each uniqueActivities as activity}
        <option value={activity}>{activity}</option>
      {/each}
    </select>
    <span class="text-sm text-gray-500">{sortedData.length} membres</span>
  </div>

  <!-- Table -->
  <div class="overflow-x-auto">
    <table class="table table-zebra table-sm w-full">
      <thead>
        <tr>
          <th><button class="font-bold" onclick={() => toggleSort('lastname')}>Nom{sortIndicator('lastname')}</button></th>
          <th><button class="font-bold" onclick={() => toggleSort('firstname')}>Prénom{sortIndicator('firstname')}</button></th>
          <th><button class="font-bold" onclick={() => toggleSort('company')}>Entreprise{sortIndicator('company')}</button></th>
          <th><button class="font-bold" onclick={() => toggleSort('email')}>Email{sortIndicator('email')}</button></th>
          <th><button class="font-bold" onclick={() => toggleSort('activities')}>Activités{sortIndicator('activities')}</button></th>
          <th><button class="font-bold" onclick={() => toggleSort('order_date')}>Inscription{sortIndicator('order_date')}</button></th>
          <th><button class="font-bold" onclick={() => toggleSort('ea')}>EA{sortIndicator('ea')}</button></th>
          <th><button class="font-bold" onclick={() => toggleSort('invoice_generated')}>Facture{sortIndicator('invoice_generated')}</button></th>
          <th><button class="font-bold" onclick={() => toggleSort('email_sent')}>Envoi{sortIndicator('email_sent')}</button></th>
        </tr>
      </thead>
      <tbody>
        {#each paginatedData as member}
          <tr>
            <td>{member.lastname}</td>
            <td>{member.firstname}</td>
            <td>{member.company || ''}</td>
            <td class="text-xs">{member.email}</td>
            <td class="text-xs">{(member.activities || []).join(', ')}</td>
            <td>{member.order_date || ''}</td>
            <td>{member.ea ? '✓' : ''}</td>
            <td>
              <button
                class="btn btn-xs"
                class:btn-success={member.invoice_generated && loadingInvoiceId !== String(member.id)}
                class:btn-ghost={!member.invoice_generated && loadingInvoiceId !== String(member.id)}
                disabled={loadingInvoiceId === String(member.id)}
                onclick={(e) => { e.stopPropagation(); toggleDropdown(`inv-${member.id}`, e); }}
              >
                {#if loadingInvoiceId === String(member.id)}
                  <span class="loading loading-spinner loading-xs"></span>
                {:else}
                  {member.invoice_generated ? '✓' : '—'}
                {/if}
              </button>
            </td>
            <td>
              <button
                class="btn btn-xs"
                class:btn-success={member.email_sent && loadingEmailId !== String(member.id)}
                class:btn-warning={member.email_error && loadingEmailId !== String(member.id)}
                class:btn-ghost={!member.email_sent && !member.email_error && loadingEmailId !== String(member.id)}
                disabled={loadingEmailId === String(member.id)}
                onclick={(e) => { e.stopPropagation(); toggleDropdown(`email-${member.id}`, e); }}
              >
                {#if loadingEmailId === String(member.id)}
                  <span class="loading loading-spinner loading-xs"></span>
                {:else if member.email_sent}
                  ✓
                {:else if member.email_error}
                  ⚠
                {:else}
                  —
                {/if}
              </button>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

  <!-- Pagination -->
  {#if totalPages > 1}
    <div class="flex justify-center">
      <div class="join">
        <button
          class="join-item btn btn-sm"
          disabled={currentPage <= 1}
          onclick={() => currentPage = Math.max(1, currentPage - 1)}
        >
          Précédent
        </button>
        {#each Array.from({ length: totalPages }, (_, i) => i + 1) as page}
          <button
            class="join-item btn btn-sm"
            class:btn-active={page === currentPage}
            onclick={() => currentPage = page}
          >
            {page}
          </button>
        {/each}
        <button
          class="join-item btn btn-sm"
          disabled={currentPage >= totalPages}
          onclick={() => currentPage = Math.min(totalPages, currentPage + 1)}
        >
          Suivant
        </button>
      </div>
    </div>
  {/if}

  <!-- Dropdown portal (fixed position, outside table overflow) -->
  {#if openDropdown}
    {@const dropdownMemberId = openDropdown.split('-').slice(1).join('-')}
    {@const dropdownType = openDropdown.startsWith('inv-') ? 'invoice' : 'email'}
    {@const member = data.find(m => String(m.id) === dropdownMemberId)}
    {#if member}
      <ul
        class="menu bg-base-100 shadow-lg rounded-box fixed z-[9999] w-48 border"
        style="left: {dropdownPos.x}px; top: {dropdownPos.y - 8}px; transform: translateY(-100%);"
        role="menu"
        onkeydown={(e) => { if (e.key === 'Escape') closeDropdowns(); }}
        onclick={(e) => e.stopPropagation()}
      >
        {#if dropdownType === 'invoice'}
          {#if member.invoice_generated}
            {#if member.invoice_date}
              <li class="menu-title text-xs">Générée le {member.invoice_date}</li>
            {/if}
            <li role="menuitem"><button class="flex items-center gap-2" onclick={() => handlePreview(member.id)}>
              <Icon name="eye" />
              Aperçu
            </button></li>
            <li role="menuitem"><button class="flex items-center gap-2" onclick={() => { onDownload?.(String(member.id)); closeDropdowns(); }}>
              <Icon name="download" />
              Télécharger
            </button></li>
            <li role="menuitem"><button class="flex items-center gap-2" onclick={() => { onRegenerateInvoice?.(String(member.id)); closeDropdowns(); }}>
              <Icon name="refresh" />
              Regénérer
            </button></li>
            <li role="menuitem"><button class="flex items-center gap-2 text-error" onclick={() => { onDeleteInvoice?.(String(member.id)); closeDropdowns(); }}>
              <Icon name="trash" />
              Supprimer
            </button></li>
          {:else}
            <li role="menuitem"><button class="flex items-center gap-2" onclick={() => { onGenerateInvoice?.(String(member.id)); closeDropdowns(); }}>
              <Icon name="document" />
              Générer
            </button></li>
          {/if}
        {:else}
          {#if member.email_sent && member.email_date}
            <li class="menu-title text-xs">Envoyé le {member.email_date}</li>
          {/if}
          {#if member.invoice_generated && !member.email_sent}
            <li role="menuitem"><button class="flex items-center gap-2" onclick={() => { onSendEmail?.(String(member.id)); closeDropdowns(); }}>
              <Icon name="mail" />
              Envoyer
            </button></li>
          {:else if member.email_sent}
            <li role="menuitem"><button class="flex items-center gap-2" onclick={() => { onSendEmail?.(String(member.id)); closeDropdowns(); }}>
              <Icon name="mail" />
              Renvoyer
            </button></li>
          {:else}
            <li class="disabled"><span class="text-gray-400 text-xs">Générer la facture d'abord</span></li>
          {/if}
        {/if}
      </ul>
    {/if}
  {/if}

  <!-- Preview modal -->
  {#if previewMemberId !== null}
    <InvoicePreview
      memberId={previewMemberId}
      open={showPreview}
      onClose={handleClosePreview}
    />
  {/if}
</div>
