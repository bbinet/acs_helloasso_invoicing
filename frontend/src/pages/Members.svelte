<script lang="ts">
  import { onMount } from 'svelte';
  import Layout from '../components/Layout.svelte';
  import MemberTable from '../components/MemberTable.svelte';
  import { getMembers, generateInvoice, sendEmail, downloadInvoice, deleteInvoice, batchGenerateInvoices, batchSendEmails } from '../lib/api';

  let members: any[] = $state([]);
  let alertMessage = $state('');
  let alertType = $state<'success' | 'error'>('success');
  let alertTimeout: ReturnType<typeof setTimeout> | null = null;

  function showAlert(message: string, type: 'success' | 'error') {
    alertMessage = message;
    alertType = type;
    if (alertTimeout) clearTimeout(alertTimeout);
    alertTimeout = setTimeout(() => { alertMessage = ''; }, 5000);
  }

  async function loadMembers() {
    members = await getMembers({refund_filtered: 'true'});
  }

  async function handleGenerateInvoice(memberId: string) {
    try {
      await generateInvoice(memberId);
      showAlert('Facture générée avec succès', 'success');
      await loadMembers();
    } catch (err: any) {
      showAlert(err.detail || 'Erreur lors de la génération', 'error');
    }
  }

  async function handleSendEmail(memberId: string) {
    try {
      await sendEmail(memberId);
      showAlert('Email envoyé avec succès', 'success');
      await loadMembers();
    } catch (err: any) {
      showAlert(err.detail || "Erreur lors de l'envoi", 'error');
    }
  }

  async function handleDownload(memberId: string) {
    window.open(`/api/invoices/${memberId}/download`, '_blank');
  }

  async function handleDeleteInvoice(memberId: string) {
    try {
      await deleteInvoice(memberId);
      showAlert('Facture supprimée', 'success');
      await loadMembers();
    } catch (err: any) {
      showAlert(err.detail || 'Erreur lors de la suppression', 'error');
    }
  }

  async function handleRegenerateInvoice(memberId: string) {
    try {
      await deleteInvoice(memberId);
      await generateInvoice(memberId);
      showAlert('Facture regénérée avec succès', 'success');
      await loadMembers();
    } catch (err: any) {
      showAlert(err.detail || 'Erreur lors de la regénération', 'error');
    }
  }

  async function handleBatchGenerate(memberIds: string[]) {
    const result = await batchGenerateInvoices(memberIds.map(Number));
    return result;
  }

  async function handleBatchSend(memberIds: string[]) {
    const result = await batchSendEmails(memberIds.map(Number));
    return result;
  }

  function handleBatchComplete() {
    loadMembers();
  }

  onMount(() => {
    loadMembers();
  });
</script>

<Layout>
  <h1 class="text-2xl font-bold mb-6">Membres</h1>

  {#if alertMessage}
    <div class="alert mb-4" class:alert-success={alertType === 'success'} class:alert-error={alertType === 'error'}>
      <span>{alertMessage}</span>
      <button class="btn btn-ghost btn-xs" onclick={() => alertMessage = ''}>✕</button>
    </div>
  {/if}

  <MemberTable
    data={members}
    onGenerateInvoice={handleGenerateInvoice}
    onSendEmail={handleSendEmail}
    onDownload={handleDownload}
    onDeleteInvoice={handleDeleteInvoice}
    onRegenerateInvoice={handleRegenerateInvoice}
    onBatchGenerate={handleBatchGenerate}
    onBatchSend={handleBatchSend}
    onBatchComplete={handleBatchComplete}
  />
</Layout>
