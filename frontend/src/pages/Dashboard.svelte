<script lang="ts">
  import { onMount } from 'svelte';
  import Layout from '../components/Layout.svelte';
  import { getMembers, refreshCampaigns, getSummary } from '../lib/api';

  let members: any[] = $state([]);
  let summary: { activities: any[]; total: number } | null = $state(null);
  let refreshing = $state(false);
  let expandedActivities: Set<string> = $state(new Set());
  let sortBy = $state<'count' | 'name'>('count');
  let sortDir = $state<'asc' | 'desc'>('desc');

  let totalMembers = $derived(members.length);
  let invoicesGenerated = $derived(members.filter(m => m.invoice_generated).length);
  let emailsSent = $derived(members.filter(m => m.email_sent).length);

  let sortedActivities = $derived.by(() => {
    if (!summary) return [];
    return [...summary.activities].sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1;
      if (sortBy === 'count') return (a.count - b.count) * dir;
      return a.name.localeCompare(b.name) * dir;
    });
  });

  async function loadData() {
    const [membersData, summaryData] = await Promise.all([
      getMembers({refund_filtered: 'true'}),
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

  function toggleSort(column: 'count' | 'name') {
    if (sortBy === column) {
      sortDir = sortDir === 'asc' ? 'desc' : 'asc';
    } else {
      sortBy = column;
      sortDir = column === 'count' ? 'desc' : 'asc';
    }
  }

  function sortIndicator(column: string) {
    if (sortBy !== column) return '';
    return sortDir === 'asc' ? ' ↑' : ' ↓';
  }

  function toggleActivity(name: string) {
    const next = new Set(expandedActivities);
    if (next.has(name)) { next.delete(name); } else { next.add(name); }
    expandedActivities = next;
  }

  onMount(() => { loadData(); });
</script>

<Layout>
  <h1 class="text-2xl font-bold mb-6">Dashboard</h1>

  <!-- Stats -->
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

  <!-- Activity Summary -->
  {#if summary}
    <h2 class="text-xl font-semibold mb-4">Résumé par activité</h2>
    <div class="overflow-x-auto">
      <table class="table w-full">
        <thead>
          <tr>
            <th>
              <button class="font-bold" onclick={() => toggleSort('name')}>
                Activité{sortIndicator('name')}
              </button>
            </th>
            <th>
              <button class="font-bold" onclick={() => toggleSort('count')}>
                Nombre de membres{sortIndicator('count')}
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          {#each sortedActivities as activity}
            <tr class="hover" onclick={() => toggleActivity(activity.name)}>
              <td>{activity.name}</td>
              <td>{activity.count}</td>
            </tr>
            {#if expandedActivities.has(activity.name)}
              <tr>
                <td colspan="2" class="bg-base-200 pl-8">
                  <ul class="list-disc list-inside">
                    {#each activity.members as member}
                      <li>{member}</li>
                    {/each}
                  </ul>
                </td>
              </tr>
            {/if}
          {/each}
          <tr class="font-bold">
            <td>Total (inscriptions)</td>
            <td>{sortedActivities.reduce((sum, a) => sum + a.count, 0)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  {/if}
</Layout>
