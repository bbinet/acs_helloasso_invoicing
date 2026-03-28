<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Chart, ArcElement, Tooltip, Legend, DoughnutController } from 'chart.js';
  import Layout from '../components/Layout.svelte';
  import { getMembers } from '../lib/api';
  import type { Member } from '../lib/types';
  import { CHART_COLORS, NO_ACTIVITY_LABEL, THEME } from '../lib/constants';

  Chart.register(ArcElement, Tooltip, Legend, DoughnutController);

  let members: Member[] = $state([]);
  let expandedActivities = $state(new Set<string>());
  let sortBy = $state<'count' | 'name'>('count');
  let sortDir = $state<'asc' | 'desc'>('desc');
  let hoveredActivity: string | null = $state(null);

  let chartCanvas: HTMLCanvasElement;
  let chartContainer: HTMLDivElement;
  let chart: Chart | null = null;
  let resizeObserver: ResizeObserver | null = null;

  // Stats
  const totalMembers = $derived(members.length);
  const membersEA = $derived(members.filter(m => m.ea).length);
  const invoicesGenerated = $derived(members.filter(m => m.invoice_generated).length);
  const emailsSent = $derived(members.filter(m => m.email_sent).length);

  // Activity summary
  const activitySummary = $derived.by(() => {
    if (members.length === 0) return [];

    const map = new Map<string, { count: number; members: string[] }>();

    for (const member of members) {
      const memberName = `${member.firstname} ${member.lastname}`;
      const activities = member.activities?.length ? member.activities : [NO_ACTIVITY_LABEL];

      for (const activity of activities) {
        const entry = map.get(activity) ?? { count: 0, members: [] };
        entry.count++;
        entry.members.push(memberName);
        map.set(activity, entry);
      }
    }

    return Array.from(map.entries())
      .map(([name, data]) => ({ name, ...data }))
      .sort((a, b) => b.count - a.count);
  });

  const sortedActivities = $derived.by(() => {
    const dir = sortDir === 'asc' ? 1 : -1;
    return [...activitySummary].sort((a, b) =>
      sortBy === 'count' ? (a.count - b.count) * dir : a.name.localeCompare(b.name) * dir
    );
  });

  const totalInscriptions = $derived(activitySummary.reduce((sum, a) => sum + a.count, 0));

  const centerTextPlugin = {
    id: 'centerText',
    afterDraw(chart: Chart) {
      const { ctx, chartArea } = chart;
      if (!chartArea) return;

      const centerX = (chartArea.left + chartArea.right) / 2;
      const centerY = (chartArea.top + chartArea.bottom) / 2;
      const radius = Math.min(chartArea.right - chartArea.left, chartArea.bottom - chartArea.top) / 2;
      const total = (chart.data.datasets[0].data as number[]).reduce((a, b) => a + b, 0);

      const numberSize = Math.max(14, radius * 0.22);
      const labelSize = Math.max(9, radius * 0.08);
      const gap = radius * 0.08;

      ctx.save();
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      ctx.font = `bold ${numberSize}px sans-serif`;
      ctx.fillStyle = '#e4e4e7';
      ctx.fillText(String(total), centerX, centerY - gap);

      ctx.font = `${labelSize}px sans-serif`;
      ctx.fillStyle = THEME.textMuted;
      ctx.fillText('inscriptions', centerX, centerY + gap + labelSize / 2);

      ctx.restore();
    }
  };

  async function updateChart() {
    if (activitySummary.length === 0) return;
    await tick();
    if (!chartCanvas) return;

    const data = {
      labels: activitySummary.map(a => a.name),
      datasets: [{
        data: activitySummary.map(a => a.count),
        backgroundColor: CHART_COLORS.slice(0, activitySummary.length),
        borderWidth: 2,
        borderColor: THEME.borderColor,
        hoverBorderWidth: 4,
        hoverBorderColor: '#ffffff',
        hoverOffset: 8,
      }]
    };

    if (chart) {
      chart.data = data;
      chart.update();
      return;
    }

    chart = new Chart(chartCanvas, {
      type: 'doughnut',
      data,
      plugins: [centerTextPlugin],
      options: {
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 1,
        cutout: '60%',
        layout: { padding: 15 },
        onHover: (_event, elements) => {
          hoveredActivity = elements.length > 0 ? activitySummary[elements[0].index]?.name ?? null : null;
        },
        onClick: (_event, elements) => {
          if (elements.length === 0) return;
          const name = activitySummary[elements[0].index]?.name;
          if (!name) return;
          expandedActivities = expandedActivities.has(name) ? new Set() : new Set([name]);
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${ctx.raw} membres`
            }
          }
        }
      }
    });

    resizeObserver?.observe(chartContainer);
  }

  async function loadData() {
    members = await getMembers({ refund_filtered: 'true' });
    await updateChart();
  }

  function toggleSort(column: 'count' | 'name') {
    if (sortBy === column) {
      sortDir = sortDir === 'asc' ? 'desc' : 'asc';
    } else {
      sortBy = column;
      sortDir = column === 'count' ? 'desc' : 'asc';
    }
  }

  function getActivityColor(name: string): string {
    const index = activitySummary.findIndex(a => a.name === name);
    return CHART_COLORS[index % CHART_COLORS.length];
  }

  function handleRowHover(name: string | null) {
    hoveredActivity = name;
    if (!chart) return;

    if (name === null) {
      chart.setActiveElements([]);
    } else {
      const index = activitySummary.findIndex(a => a.name === name);
      if (index >= 0) {
        chart.setActiveElements([{ datasetIndex: 0, index }]);
      }
    }
    chart.update();
  }

  function toggleActivity(name: string) {
    const next = new Set(expandedActivities);
    next.has(name) ? next.delete(name) : next.add(name);
    expandedActivities = next;
  }

  onMount(() => {
    loadData();
    window.addEventListener('helloasso-refreshed', loadData);
    resizeObserver = new ResizeObserver(() => chart?.resize());
  });

  onDestroy(() => {
    window.removeEventListener('helloasso-refreshed', loadData);
    resizeObserver?.disconnect();
    chart?.destroy();
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
      <div class="stat-title">Espace Emile Allais</div>
      <div class="stat-value">{membersEA}</div>
    </div>
    <div class="stat">
      <div class="stat-title">Factures générées</div>
      <div class="stat-value">
        {invoicesGenerated}
        <span class="text-sm text-base-content/50">{Math.round(invoicesGenerated / totalMembers * 100)}%</span>
      </div>
    </div>
    <div class="stat">
      <div class="stat-title">Factures envoyées</div>
      <div class="stat-value">
        {emailsSent}
        <span class="text-sm text-base-content/50">{invoicesGenerated ? Math.round(emailsSent / invoicesGenerated * 100) : 0}%</span>
      </div>
    </div>
  </div>

  {#if activitySummary.length > 0}
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6 items-stretch">
      <div class="card bg-base-100 shadow h-full">
        <div class="card-body flex flex-col">
          <h2 class="card-title">Répartition par activité</h2>
          <div bind:this={chartContainer} class="flex-1 flex items-start justify-center p-6">
            <canvas bind:this={chartCanvas} onmouseleave={() => hoveredActivity = null}></canvas>
          </div>
        </div>
      </div>

      <div class="card bg-base-100 shadow">
        <div class="card-body">
          <h2 class="card-title">Détail par activité</h2>
          <div class="overflow-x-auto">
            <table class="table w-full">
              <thead>
                <tr>
                  <th>
                    <button class="font-bold" onclick={() => toggleSort('name')}>
                      Activité{sortBy === 'name' ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
                    </button>
                  </th>
                  <th>
                    <button class="font-bold" onclick={() => toggleSort('count')}>
                      Nombre de membres{sortBy === 'count' ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody>
                {#each sortedActivities as activity}
                  <tr
                    class="cursor-pointer transition-colors {hoveredActivity === activity.name ? 'bg-base-300' : 'hover:bg-base-200'}"
                    onclick={() => toggleActivity(activity.name)}
                    onmouseenter={() => handleRowHover(activity.name)}
                    onmouseleave={() => handleRowHover(null)}
                  >
                    <td>
                      <div class="flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full flex-shrink-0" style="background-color: {getActivityColor(activity.name)}"></span>
                        {activity.name}
                      </div>
                    </td>
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
                  <td>{totalInscriptions}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  {/if}
</Layout>
