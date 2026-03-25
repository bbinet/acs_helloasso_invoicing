<script lang="ts">
  import { onMount } from 'svelte';
  import Layout from '../components/Layout.svelte';
  import { getSummary } from '../lib/api';

  let summary: { activities: any[]; total: number } | null = $state(null);
  let loading = $state(true);
  let expandedActivities: Set<string> = $state(new Set());
  let sortBy = $state<'count' | 'name'>('count');
  let sortDir = $state<'asc' | 'desc'>('desc');

  let sortedActivities = $derived.by(() => {
    if (!summary) return [];
    return [...summary.activities].sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1;
      if (sortBy === 'count') {
        return (a.count - b.count) * dir;
      } else {
        return a.name.localeCompare(b.name) * dir;
      }
    });
  });

  onMount(async () => {
    try {
      summary = await getSummary();
    } catch {
      // ignore
    } finally {
      loading = false;
    }
  });

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
    if (next.has(name)) {
      next.delete(name);
    } else {
      next.add(name);
    }
    expandedActivities = next;
  }
</script>

<Layout>
  <h1 class="text-2xl font-bold mb-4">Résumé</h1>

  {#if loading}
    <span class="loading loading-spinner loading-lg"></span>
  {:else if summary}
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
            <tr class="cursor-pointer hover" onclick={() => toggleActivity(activity.name)}>
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
            <td>Total</td>
            <td>{summary.total}</td>
          </tr>
        </tbody>
      </table>
    </div>
  {/if}
</Layout>
