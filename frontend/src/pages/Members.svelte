<script lang="ts">
  import { onMount } from 'svelte';
  import Layout from '../components/Layout.svelte';
  import MemberTable from '../components/MemberTable.svelte';
  import { getMembers, generateInvoice, sendEmail, downloadInvoice, exportCSV } from '../lib/api';

  let members: any[] = $state([]);
  let alertMessage = $state('');
  let alertType = $state<'success' | 'error'>('success');

  async function loadMembers() {
    members = await getMembers();
  }

  async function handleGenerateInvoice(memberId: string) {
    try {
      await generateInvoice(memberId);
      alertMessage = 'Facture generee avec succes';
      alertType = 'success';
      await loadMembers();
    } catch (err: any) {
      alertMessage = err.detail || 'Erreur lors de la generation';
      alertType = 'error';
    }
  }

  async function handleSendEmail(memberId: string) {
    try {
      await sendEmail(memberId);
      alertMessage = 'Email envoye avec succes';
      alertType = 'success';
      await loadMembers();
    } catch (err: any) {
      alertMessage = err.detail || "Erreur lors de l'envoi";
      alertType = 'error';
    }
  }

  async function handleDownload(memberId: string) {
    try {
      const result = await downloadInvoice(memberId);
      // If the API returns a URL or blob, handle download
      if (result.url) {
        window.open(result.url, '_blank');
      }
    } catch (err: any) {
      alertMessage = err.detail || 'Erreur lors du telechargement';
      alertType = 'error';
    }
  }

  async function handleExportCSV() {
    try {
      const result = await exportCSV();
      if (result.url) {
        window.open(result.url, '_blank');
      }
    } catch (err: any) {
      alertMessage = err.detail || "Erreur lors de l'export CSV";
      alertType = 'error';
    }
  }

  onMount(() => {
    loadMembers();
  });
</script>

<Layout>
  <div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold">Membres</h1>
    <button class="btn btn-outline btn-sm" onclick={handleExportCSV}>
      Exporter CSV
    </button>
  </div>

  {#if alertMessage}
    <div class="alert alert-{alertType} mb-4">
      <span>{alertMessage}</span>
      <button class="btn btn-ghost btn-xs" onclick={() => alertMessage = ''}>x</button>
    </div>
  {/if}

  <MemberTable
    data={members}
    onGenerateInvoice={handleGenerateInvoice}
    onSendEmail={handleSendEmail}
    onDownload={handleDownload}
  />
</Layout>
