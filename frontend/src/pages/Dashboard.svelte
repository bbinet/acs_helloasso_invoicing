<script lang="ts">
  import { onMount } from 'svelte';
  import Layout from '../components/Layout.svelte';
  import { getMembers, refreshCampaigns, getSummary } from '../lib/api';

  let members: any[] = $state([]);
  let summary: any = $state(null);
  let refreshing = $state(false);

  let totalMembers = $derived(members.length);
  let invoicesGenerated = $derived(members.filter(m => m.invoice_generated).length);
  let emailsSent = $derived(members.filter(m => m.email_sent).length);

  async function loadData() {
    const [membersData, summaryData] = await Promise.all([
      getMembers(),
      getSummary().catch(() => null),
    ]);
    members = membersData;
    summary = summaryData;
  }

  async function handleRefresh() {
    refreshing = true;
    try {
      await refreshCampaigns();
      await loadData();
    } finally {
      refreshing = false;
    }
  }

  onMount(() => {
    loadData();
  });
</script>

<Layout>
  <h1 class="text-2xl font-bold mb-6">Dashboard</h1>

  <div class="stats shadow mb-6">
    <div class="stat">
      <div class="stat-title">Total membres</div>
      <div class="stat-value">{totalMembers}</div>
    </div>
    <div class="stat">
      <div class="stat-title">Factures générées</div>
      <div class="stat-value">{invoicesGenerated}</div>
    </div>
    <div class="stat">
      <div class="stat-title">Emails envoyés</div>
      <div class="stat-value">{emailsSent}</div>
    </div>
  </div>

  <button class="btn btn-primary mb-6" onclick={handleRefresh} disabled={refreshing}>
    {#if refreshing}
      <span class="loading loading-spinner loading-sm"></span>
    {/if}
    Rafraîchir depuis HelloAsso
  </button>

  {#if summary?.recent_activity?.length}
    <div class="overflow-x-auto">
      <h2 class="text-lg font-semibold mb-2">Activité récente</h2>
      <table class="table table-zebra">
        <thead>
          <tr>
            <th>Date</th>
            <th>Action</th>
            <th>Membre</th>
          </tr>
        </thead>
        <tbody>
          {#each summary.recent_activity as item}
            <tr>
              <td>{item.date}</td>
              <td>{item.action}</td>
              <td>{item.member}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</Layout>
