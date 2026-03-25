<script lang="ts">
  import { downloadInvoice } from '../lib/api';

  let {
    memberId,
    open = false,
    onClose,
  }: {
    memberId: number;
    open: boolean;
    onClose?: () => void;
  } = $props();

  async function handleDownload() {
    await downloadInvoice(String(memberId));
  }
</script>

{#if open}
  <dialog class="modal modal-open">
    <div class="modal-box w-11/12 max-w-5xl h-[80vh]">
      <iframe
        src="/api/invoices/{memberId}/preview"
        class="w-full h-full border-0"
        title="Apercu facture"
      ></iframe>
      <div class="modal-action">
        <button class="btn btn-primary" onclick={handleDownload}>Telecharger PDF</button>
        <button class="btn" onclick={() => onClose?.()}>Fermer</button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button onclick={() => onClose?.()}>close</button>
    </form>
  </dialog>
{/if}
