<script lang="ts">
  import { onMount, onDestroy, tick } from 'svelte';
  import {
    Chart,
    BarController,
    BarElement,
    CategoryScale,
    LinearScale,
    Tooltip,
    Legend,
    LineController,
    LineElement,
    PointElement,
    Filler,
  } from 'chart.js';
  import Layout from '../components/Layout.svelte';
  import { getMembers } from '../lib/api';
  import type { Member } from '../lib/types';
  import { CHART_COLORS, MONTH_NAMES_FR, NO_ACTIVITY_LABEL, THEME } from '../lib/constants';
  import { createScales, createLegend, baseChartOptions } from '../lib/chart-utils';

  Chart.register(
    BarController, BarElement, CategoryScale, LinearScale,
    Tooltip, Legend, LineController, LineElement, PointElement, Filler
  );

  let members: Member[] = $state([]);
  let charts: Chart[] = [];

  let evolutionCanvas: HTMLCanvasElement;
  let monthlyCanvas: HTMLCanvasElement;
  let barCanvas: HTMLCanvasElement;
  let stackedCanvas: HTMLCanvasElement;
  let multiActivitiesCanvas: HTMLCanvasElement;

  // Activities aggregation
  const activitiesData = $derived.by(() => {
    if (members.length === 0) return [];

    const map = new Map<string, { total: number; withInvoice: number; emailSent: number }>();

    for (const member of members) {
      const activities = member.activities?.length ? member.activities : [NO_ACTIVITY_LABEL];

      for (const activity of activities) {
        const entry = map.get(activity) ?? { total: 0, withInvoice: 0, emailSent: 0 };
        entry.total++;
        if (member.invoice_generated) entry.withInvoice++;
        if (member.email_sent) entry.emailSent++;
        map.set(activity, entry);
      }
    }

    return Array.from(map.entries())
      .map(([name, data]) => ({ name, ...data }))
      .sort((a, b) => b.total - a.total);
  });

  // Evolution data (cumulative)
  const evolutionData = $derived.by(() => {
    if (members.length === 0) return { labels: [], inscriptions: [], emails: [] };

    const inscriptionMap = new Map<string, number>();
    const emailMap = new Map<string, number>();

    for (const member of members) {
      const orderDate = member.order_date?.split('T')[0];
      if (orderDate) {
        inscriptionMap.set(orderDate, (inscriptionMap.get(orderDate) || 0) + 1);
      }
      if (member.email_sent && member.email_date) {
        const emailDate = member.email_date.split('T')[0];
        emailMap.set(emailDate, (emailMap.get(emailDate) || 0) + 1);
      }
    }

    const sortedDates = [...new Set([...inscriptionMap.keys(), ...emailMap.keys()])].sort();

    let cumInscriptions = 0;
    let cumEmails = 0;

    return sortedDates.reduce(
      (acc, date) => {
        cumInscriptions += inscriptionMap.get(date) || 0;
        cumEmails += emailMap.get(date) || 0;
        const [, month, day] = date.split('-');
        acc.labels.push(`${day}/${month}`);
        acc.inscriptions.push(cumInscriptions);
        acc.emails.push(cumEmails);
        return acc;
      },
      { labels: [] as string[], inscriptions: [] as number[], emails: [] as number[] }
    );
  });

  // Monthly data
  const monthlyData = $derived.by(() => {
    if (members.length === 0) return { labels: [], data: [] };

    const map = new Map<string, number>();

    for (const member of members) {
      const date = member.order_date?.split('T')[0];
      if (date) {
        const [year, month] = date.split('-');
        const key = `${year}-${month}`;
        map.set(key, (map.get(key) || 0) + 1);
      }
    }

    return [...map.keys()].sort().reduce(
      (acc, key) => {
        const [year, month] = key.split('-');
        acc.labels.push(`${MONTH_NAMES_FR[parseInt(month) - 1]} ${year.slice(2)}`);
        acc.data.push(map.get(key)!);
        return acc;
      },
      { labels: [] as string[], data: [] as number[] }
    );
  });

  // Multi-activities data
  const multiActivitiesData = $derived.by(() => {
    const counts = [0, 0, 0, 0]; // 0, 1, 2, 3+

    for (const member of members) {
      const n = member.activities?.length ?? 0;
      counts[Math.min(n, 3)]++;
    }

    return {
      labels: ['Aucune', '1 activité', '2 activités', '3+ activités'],
      data: counts,
    };
  });

  function destroyCharts() {
    charts.forEach(c => c.destroy());
    charts = [];
  }

  async function createCharts() {
    await tick();
    if (!evolutionCanvas || activitiesData.length === 0) return;

    destroyCharts();

    // Evolution line chart
    charts.push(new Chart(evolutionCanvas, {
      type: 'line',
      data: {
        labels: evolutionData.labels,
        datasets: [
          {
            label: 'Inscriptions',
            data: evolutionData.inscriptions,
            borderColor: '#6366f1',
            backgroundColor: 'rgba(99, 102, 241, 0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 2,
            pointHoverRadius: 5,
          },
          {
            label: 'Factures envoyées',
            data: evolutionData.emails,
            borderColor: '#22c55e',
            backgroundColor: 'rgba(34, 197, 94, 0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 2,
            pointHoverRadius: 5,
          }
        ]
      },
      options: {
        ...baseChartOptions,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: createLegend(),
          tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.raw}` } }
        },
        scales: createScales({ xRotation: 45 }),
      }
    }));

    // Monthly bar chart
    charts.push(new Chart(monthlyCanvas, {
      type: 'bar',
      data: {
        labels: monthlyData.labels,
        datasets: [{
          label: 'Inscriptions',
          data: monthlyData.data,
          backgroundColor: '#6366f1',
          borderWidth: 0,
        }]
      },
      options: {
        ...baseChartOptions,
        plugins: {
          legend: createLegend({ display: false }),
          tooltip: { callbacks: { label: ctx => ` ${ctx.raw} inscriptions` } }
        },
        scales: createScales({ xGrid: false }),
      }
    }));

    // Horizontal bar chart
    charts.push(new Chart(barCanvas, {
      type: 'bar',
      data: {
        labels: activitiesData.map(a => a.name),
        datasets: [{
          label: 'Membres',
          data: activitiesData.map(a => a.total),
          backgroundColor: CHART_COLORS.slice(0, activitiesData.length),
          borderWidth: 0,
        }]
      },
      options: {
        ...baseChartOptions,
        indexAxis: 'y',
        plugins: {
          legend: createLegend({ display: false }),
          tooltip: { callbacks: { label: ctx => ` ${ctx.raw} membres` } }
        },
        scales: createScales({ yGrid: false }),
      }
    }));

    // Stacked bar chart
    charts.push(new Chart(stackedCanvas, {
      type: 'bar',
      data: {
        labels: activitiesData.map(a => a.name),
        datasets: [
          {
            label: 'Facture envoyée',
            data: activitiesData.map(a => a.emailSent),
            backgroundColor: '#22c55e',
          },
          {
            label: 'Facture générée',
            data: activitiesData.map(a => a.withInvoice - a.emailSent),
            backgroundColor: '#3b82f6',
          },
          {
            label: 'Sans facture',
            data: activitiesData.map(a => a.total - a.withInvoice),
            backgroundColor: '#6b7280',
          },
        ]
      },
      options: {
        ...baseChartOptions,
        indexAxis: 'y',
        plugins: {
          legend: createLegend({ position: 'bottom' }),
        },
        scales: createScales({ stacked: true, yGrid: false }),
      }
    }));

    // Multi-activities bar chart
    charts.push(new Chart(multiActivitiesCanvas, {
      type: 'bar',
      data: {
        labels: multiActivitiesData.labels,
        datasets: [{
          label: 'Membres',
          data: multiActivitiesData.data,
          backgroundColor: ['#6b7280', '#6366f1', '#8b5cf6', '#a855f7'],
          borderWidth: 0,
        }]
      },
      options: {
        ...baseChartOptions,
        plugins: {
          legend: createLegend({ display: false }),
          tooltip: { callbacks: { label: ctx => ` ${ctx.raw} membres` } }
        },
        scales: createScales({ xGrid: false }),
      }
    }));
  }

  async function loadData() {
    members = await getMembers({ refund_filtered: 'true' });
    await createCharts();
  }

  onMount(() => {
    loadData();
    window.addEventListener('helloasso-refreshed', loadData);
  });

  onDestroy(() => {
    window.removeEventListener('helloasso-refreshed', loadData);
    destroyCharts();
  });
</script>

<Layout>
  <h1 class="text-2xl font-bold mb-6">Graphiques</h1>

  <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
    <div class="card bg-base-100 shadow xl:col-span-2">
      <div class="card-body">
        <h2 class="card-title">Évolution des inscriptions</h2>
        <div class="h-64">
          <canvas bind:this={evolutionCanvas}></canvas>
        </div>
      </div>
    </div>

    <div class="card bg-base-100 shadow">
      <div class="card-body">
        <h2 class="card-title">Membres par activité</h2>
        <div class="h-96">
          <canvas bind:this={barCanvas}></canvas>
        </div>
      </div>
    </div>

    <div class="card bg-base-100 shadow">
      <div class="card-body">
        <h2 class="card-title">Statut par activité</h2>
        <div class="h-96">
          <canvas bind:this={stackedCanvas}></canvas>
        </div>
      </div>
    </div>

    <div class="card bg-base-100 shadow">
      <div class="card-body">
        <h2 class="card-title">Inscriptions par mois</h2>
        <div class="h-64">
          <canvas bind:this={monthlyCanvas}></canvas>
        </div>
      </div>
    </div>

    <div class="card bg-base-100 shadow">
      <div class="card-body">
        <h2 class="card-title">Membres multi-activités</h2>
        <div class="h-64">
          <canvas bind:this={multiActivitiesCanvas}></canvas>
        </div>
      </div>
    </div>
  </div>
</Layout>
