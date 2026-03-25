<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import BatchProgress from './BatchProgress.svelte';
  import InvoicePreview from './InvoicePreview.svelte';

  let {
    data = [],
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
      <button class="btn btn-primary btn-sm" onclick={handleBatchGenerate}>
        Générer les factures ({sortedData.filter(m => !m.invoice_generated).length})
      </button>
    {/if}
    {#if onBatchSend}
      <button class="btn btn-secondary btn-sm" onclick={handleBatchSend}>
        Envoyer les emails ({sortedData.filter(m => m.invoice_generated && !m.email_sent).length})
      </button>
    {/if}
    <button class="btn btn-outline btn-sm" onclick={exportCSV}>
      Exporter CSV ({sortedData.length})
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
                class:btn-success={member.invoice_generated}
                class:btn-ghost={!member.invoice_generated}
                onclick={(e) => { e.stopPropagation(); toggleDropdown(`inv-${member.id}`, e); }}
              >
                {member.invoice_generated ? '✓' : '—'}
              </button>
            </td>
            <td>
              <button
                class="btn btn-xs"
                class:btn-success={member.email_sent}
                class:btn-warning={member.email_error}
                class:btn-ghost={!member.email_sent && !member.email_error}
                onclick={(e) => { e.stopPropagation(); toggleDropdown(`email-${member.id}`, e); }}
              >
                {#if member.email_sent}✓{:else if member.email_error}⚠{:else}—{/if}
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
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
              Aperçu
            </button></li>
            <li role="menuitem"><button class="flex items-center gap-2" onclick={() => { onDownload?.(member.id); closeDropdowns(); }}>
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
              Télécharger
            </button></li>
            <li role="menuitem"><button class="flex items-center gap-2" onclick={() => { onRegenerateInvoice?.(member.id); closeDropdowns(); }}>
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
              Regénérer
            </button></li>
            <li role="menuitem"><button class="flex items-center gap-2 text-error" onclick={() => { onDeleteInvoice?.(member.id); closeDropdowns(); }}>
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
              Supprimer
            </button></li>
          {:else}
            <li role="menuitem"><button class="flex items-center gap-2" onclick={() => { onGenerateInvoice?.(member.id); closeDropdowns(); }}>
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
              Générer
            </button></li>
          {/if}
        {:else}
          {#if member.email_sent && member.email_date}
            <li class="menu-title text-xs">Envoyé le {member.email_date}</li>
          {/if}
          {#if member.invoice_generated && !member.email_sent}
            <li role="menuitem"><button class="flex items-center gap-2" onclick={() => { onSendEmail?.(member.id); closeDropdowns(); }}>
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
              Envoyer
            </button></li>
          {:else if member.email_sent}
            <li role="menuitem"><button class="flex items-center gap-2" onclick={() => { onSendEmail?.(member.id); closeDropdowns(); }}>
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
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
