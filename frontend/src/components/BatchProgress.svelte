<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { getBatchInvoiceStatus, getBatchEmailStatus } from '../lib/api';

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
  let errors: string[] = $state([]);
  let intervalId: ReturnType<typeof setInterval> | null = null;

  async function poll() {
    try {
      const getStatus = type === 'invoices' ? getBatchInvoiceStatus : getBatchEmailStatus;
      const result = await getStatus(jobId);
      completed = result.completed ?? 0;
      total = result.total ?? 0;
      errors = result.errors ?? [];
      status = result.status;

      if (result.status === 'done') {
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
  <progress
    class="progress progress-primary w-full"
    value={completed}
    max={total}
  ></progress>
  <p class="text-sm">
    {#if status === 'done'}
      Termine !
    {:else}
      {completed} / {total} termine(s)
    {/if}
  </p>
  {#if errors.length > 0}
    <div class="alert alert-error">
      <ul>
        {#each errors as error}
          <li>{error}</li>
        {/each}
      </ul>
    </div>
  {/if}
</div>
