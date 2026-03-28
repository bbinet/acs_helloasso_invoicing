<script lang="ts">
  import { onMount } from 'svelte';
  import Layout from '../components/Layout.svelte';
  import MemberTable from '../components/MemberTable.svelte';
  import { getMembers, generateInvoice, sendEmail, deleteInvoice, batchGenerateInvoices, batchSendEmails } from '../lib/api';

  let members: any[] = $state([]);
  let loadingInvoiceId = $state<string | null>(null);
  let loadingEmailId = $state<string | null>(null);

  async function loadMembers() {
    members = await getMembers({refund_filtered: 'true'});
  }

  async function handleGenerateInvoice(memberId: string) {
    loadingInvoiceId = memberId;
    try {
      await generateInvoice(memberId);
      await loadMembers();
    } finally {
      loadingInvoiceId = null;
    }
  }

  async function handleSendEmail(memberId: string) {
    loadingEmailId = memberId;
    try {
      await sendEmail(memberId);
      await loadMembers();
    } finally {
      loadingEmailId = null;
    }
  }

  function handleDownload(memberId: string) {
    window.open(`/api/invoices/${memberId}/download`, '_blank');
  }

  async function handleDeleteInvoice(memberId: string) {
    loadingInvoiceId = memberId;
    try {
      await deleteInvoice(memberId);
      await loadMembers();
    } finally {
      loadingInvoiceId = null;
    }
  }

  async function handleRegenerateInvoice(memberId: string) {
    loadingInvoiceId = memberId;
    try {
      await deleteInvoice(memberId);
      await generateInvoice(memberId);
      await loadMembers();
    } finally {
      loadingInvoiceId = null;
    }
  }

  async function handleBatchGenerate(memberIds: string[]) {
    return await batchGenerateInvoices(memberIds.map(Number));
  }

  async function handleBatchSend(memberIds: string[]) {
    return await batchSendEmails(memberIds.map(Number));
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

  <MemberTable
    data={members}
    {loadingInvoiceId}
    {loadingEmailId}
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
