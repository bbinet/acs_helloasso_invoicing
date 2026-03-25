<script lang="ts">
  let {
    data = [],
    onGenerateInvoice,
    onSendEmail,
    onDownload,
  }: {
    data: any[];
    onGenerateInvoice?: (id: string) => void;
    onSendEmail?: (id: string) => void;
    onDownload?: (id: string) => void;
  } = $props();

  let sortColumn = $state('last_name');
  let sortDirection = $state<'asc' | 'desc'>('asc');
  let searchText = $state('');
  let activityFilter = $state('');
  let currentPage = $state(1);

  const PAGE_SIZE = 20;

  let uniqueActivities = $derived(
    [...new Set(data.map((m) => m.activities).filter(Boolean))].sort()
  );

  let filteredData = $derived.by(() => {
    let result = data;
    if (searchText) {
      const term = searchText.toLowerCase();
      result = result.filter(
        (m) =>
          m.last_name?.toLowerCase().includes(term) ||
          m.first_name?.toLowerCase().includes(term) ||
          m.email?.toLowerCase().includes(term) ||
          m.company?.toLowerCase().includes(term)
      );
    }
    if (activityFilter) {
      result = result.filter((m) => m.activities === activityFilter);
    }
    return result;
  });

  let sortedData = $derived.by(() => {
    const col = sortColumn;
    const dir = sortDirection === 'asc' ? 1 : -1;
    return [...filteredData].sort((a, b) => {
      const va = a[col] ?? '';
      const vb = b[col] ?? '';
      if (va < vb) return -1 * dir;
      if (va > vb) return 1 * dir;
      return 0;
    });
  });

  let totalPages = $derived(Math.max(1, Math.ceil(sortedData.length / PAGE_SIZE)));

  let paginatedData = $derived(
    sortedData.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)
  );

  function toggleSort(column: string) {
    if (sortColumn === column) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      sortColumn = column;
      sortDirection = 'asc';
    }
  }

  function handleSearch(e: Event) {
    searchText = (e.target as HTMLInputElement).value;
    currentPage = 1;
  }

  function handleActivityChange(e: Event) {
    activityFilter = (e.target as HTMLSelectElement).value;
    currentPage = 1;
  }
</script>

<div class="space-y-4">
  <!-- Filters -->
  <div class="flex flex-wrap gap-4 items-center">
    <input
      type="text"
      placeholder="Rechercher..."
      class="input input-bordered w-64"
      value={searchText}
      oninput={handleSearch}
    />
    <select class="select select-bordered" value={activityFilter} onchange={handleActivityChange}>
      <option value="">Toutes les activit&eacute;s</option>
      {#each uniqueActivities as activity}
        <option value={activity}>{activity}</option>
      {/each}
    </select>
  </div>

  <!-- Table -->
  <div class="overflow-x-auto">
    <table class="table table-zebra w-full">
      <thead>
        <tr>
          <th>#</th>
          <th><button onclick={() => toggleSort('last_name')}>Nom{sortColumn === 'last_name' ? (sortDirection === 'asc' ? ' ↑' : ' ↓') : ''}</button></th>
          <th><button onclick={() => toggleSort('first_name')}>Pr&eacute;nom{sortColumn === 'first_name' ? (sortDirection === 'asc' ? ' ↑' : ' ↓') : ''}</button></th>
          <th><button onclick={() => toggleSort('company')}>Entreprise{sortColumn === 'company' ? (sortDirection === 'asc' ? ' ↑' : ' ↓') : ''}</button></th>
          <th><button onclick={() => toggleSort('email')}>Email{sortColumn === 'email' ? (sortDirection === 'asc' ? ' ↑' : ' ↓') : ''}</button></th>
          <th>Activit&eacute;s</th>
          <th><button onclick={() => toggleSort('date')}>Date{sortColumn === 'date' ? (sortDirection === 'asc' ? ' ↑' : ' ↓') : ''}</button></th>
          <th>EA</th>
          <th>Facture</th>
          <th>Email</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {#each paginatedData as member, i}
          <tr>
            <td>{(currentPage - 1) * PAGE_SIZE + i + 1}</td>
            <td>{member.last_name}</td>
            <td>{member.first_name}</td>
            <td>{member.company || ''}</td>
            <td>{member.email}</td>
            <td>{member.activities || ''}</td>
            <td>{member.date || ''}</td>
            <td>{member.ea ? '✓' : '✗'}</td>
            <td>
              {#if member.invoice_generated}
                <span class="badge badge-success">✓</span>
              {:else}
                <span class="badge badge-error">✗</span>
              {/if}
            </td>
            <td>
              {#if member.email_sent}
                <span class="badge badge-success">✓</span>
              {:else}
                <span class="badge badge-error">✗</span>
              {/if}
            </td>
            <td class="flex gap-1">
              <button class="btn btn-xs btn-ghost" title="Générer facture" onclick={() => onGenerateInvoice?.(member.id)}>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              </button>
              <button class="btn btn-xs btn-ghost" title="Envoyer email" onclick={() => onSendEmail?.(member.id)}>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
              </button>
              <button class="btn btn-xs btn-ghost" title="Télécharger PDF" onclick={() => onDownload?.(member.id)}>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
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
          Pr&eacute;c&eacute;dent
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
</div>
