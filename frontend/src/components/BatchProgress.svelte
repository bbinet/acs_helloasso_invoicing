<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { getBatchInvoiceStatus, getBatchEmailStatus, cancelBatchInvoices, cancelBatchEmails } from '../lib/api';

  let {
    jobId,
    type,
    onComplete,
  }: {
    jobId: string;
    type: 'invoices' | 'emails';
    onComplete?: () => void;
  } = $props();

  let completed = $state(0);
  let total = $state(0);
  let status = $state('running');
  let errors: any[] = $state([]);
  let intervalId: ReturnType<typeof setInterval> | null = null;

  async function poll() {
    try {
      const getStatus = type === 'invoices' ? getBatchInvoiceStatus : getBatchEmailStatus;
      const result = await getStatus(jobId);
      completed = result.completed ?? 0;
      total = result.total ?? 0;
      errors = result.errors ?? [];
      status = result.status;

      if (result.status === 'done' || result.status === 'cancelled') {
        if (intervalId) {
          clearInterval(intervalId);
          intervalId = null;
        }
        onComplete?.();
      }
    } catch {
      // ignore poll errors
    }
  }

  async function handleCancel() {
    try {
      const cancelFn = type === 'invoices' ? cancelBatchInvoices : cancelBatchEmails;
      await cancelFn(jobId);
    } catch {
      // ignore
    }
  }

  onMount(() => {
    poll();
    intervalId = setInterval(poll, 2000);
  });

  onDestroy(() => {
    if (intervalId) {
      clearInterval(intervalId);
    }
  });
</script>

<div class="my-4 space-y-2">
  <div class="flex items-center gap-4">
    <progress
      class="progress progress-primary flex-1"
      value={completed}
      max={total}
    ></progress>
    {#if status === 'running'}
      <button class="btn btn-error btn-xs" onclick={handleCancel}>
        Arrêter
      </button>
    {/if}
  </div>
  <p class="text-sm">
    {#if status === 'done'}
      Terminé ! ({completed}/{total})
    {:else if status === 'cancelled'}
      Annulé ({completed}/{total})
    {:else}
      {completed} / {total} terminé(s)
    {/if}
  </p>
  {#if errors.length > 0}
    <div class="alert alert-error text-sm">
      <ul>
        {#each errors as err}
          <li>{typeof err === 'string' ? err : err.error || JSON.stringify(err)}</li>
        {/each}
      </ul>
    </div>
  {/if}
</div>
