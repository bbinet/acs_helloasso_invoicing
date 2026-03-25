<script lang="ts">
  import { onMount } from 'svelte';
  import Layout from '../components/Layout.svelte';
  import BatchProgress from '../components/BatchProgress.svelte';
  import InvoicePreview from '../components/InvoicePreview.svelte';
  import { getMembers, batchGenerateInvoices, batchSendEmails, generateInvoice, sendEmail, downloadInvoice } from '../lib/api';

  let members: any[] = $state([]);
  let loading = $state(true);

  // Batch state
  let batchJobId = $state<string | null>(null);
  let batchType = $state<'invoices' | 'emails'>('invoices');
  let showBatchProgress = $state(false);

  // Preview state
  let previewMemberId = $state<number | null>(null);
  let showPreview = $state(false);

  onMount(async () => {
    try {
      members = await getMembers();
    } catch {
      // ignore
    } finally {
      loading = false;
    }
  });

  async function handleBatchGenerate() {
    try {
      const result = await batchGenerateInvoices();
      batchJobId = result.job_id;
      batchType = 'invoices';
      showBatchProgress = true;
    } catch {
      // ignore
    }
  }

  async function handleBatchSend() {
    try {
      const result = await batchSendEmails();
      batchJobId = result.job_id;
      batchType = 'emails';
      showBatchProgress = true;
    } catch {
      // ignore
    }
  }

  function handleBatchComplete() {
    // Refresh members to get updated statuses
    getMembers().then((data) => {
      members = data;
    });
  }

  function handlePreview(memberId: string) {
    previewMemberId = Number(memberId);
    showPreview = true;
  }

  function handleClosePreview() {
    showPreview = false;
    previewMemberId = null;
  }

  async function handleGenerateInvoice(memberId: string) {
    try {
      await generateInvoice(memberId);
      members = await getMembers();
    } catch {
      // ignore
    }
  }

  async function handleSendEmail(memberId: string) {
    try {
      await sendEmail(memberId);
      members = await getMembers();
    } catch {
      // ignore
    }
  }

  async function handleDownload(memberId: string) {
    try {
      await downloadInvoice(memberId);
    } catch {
      // ignore
    }
  }
</script>

<Layout>
  <h1 class="text-2xl font-bold mb-4">Factures</h1>

  <!-- Batch actions -->
  <div class="flex gap-2 mb-4">
    <button class="btn btn-primary" onclick={handleBatchGenerate}>
      Générer toutes les factures
    </button>
    <button class="btn btn-secondary" onclick={handleBatchSend}>
      Envoyer tous les emails
    </button>
  </div>

  <!-- Batch progress -->
  {#if showBatchProgress && batchJobId}
    <BatchProgress
      jobId={batchJobId}
      type={batchType}
      onComplete={handleBatchComplete}
    />
  {/if}

  <!-- Members table -->
  {#if loading}
    <span class="loading loading-spinner loading-lg"></span>
  {:else}
    <div class="overflow-x-auto">
      <table class="table table-zebra w-full">
        <thead>
          <tr>
            <th>Nom</th>
            <th>Prénom</th>
            <th>Facture</th>
            <th>Email</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {#each members as member}
            <tr>
              <td>{member.last_name}</td>
              <td>{member.first_name}</td>
              <td>
                {#if member.invoice_generated}
                  <span class="badge badge-success">&#10003;</span>
                {:else}
                  <span class="badge badge-error">&#10007;</span>
                {/if}
              </td>
              <td>
                {#if member.email_sent}
                  <span class="badge badge-success">&#10003;</span>
                {:else}
                  <span class="badge badge-error">&#10007;</span>
                {/if}
              </td>
              <td class="flex gap-1">
                <button
                  class="btn btn-xs btn-ghost"
                  title="Aperçu"
                  onclick={() => handlePreview(member.id)}
                >
                  Aperçu
                </button>
                <button
                  class="btn btn-xs btn-ghost"
                  title="Télécharger"
                  onclick={() => handleDownload(member.id)}
                >
                  Télécharger
                </button>
                <button
                  class="btn btn-xs btn-ghost"
                  title="Générer facture"
                  onclick={() => handleGenerateInvoice(member.id)}
                >
                  Générer
                </button>
                <button
                  class="btn btn-xs btn-ghost"
                  title="Envoyer email"
                  onclick={() => handleSendEmail(member.id)}
                >
                  Envoyer
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}

  <!-- Preview modal -->
  {#if previewMemberId !== null}
    <InvoicePreview
      memberId={previewMemberId}
      open={showPreview}
      onClose={handleClosePreview}
    />
  {/if}
</Layout>
