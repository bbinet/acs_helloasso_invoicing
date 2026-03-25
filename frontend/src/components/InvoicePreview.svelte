<script lang="ts">
  let {
    memberId,
    open = false,
    onClose,
  }: {
    memberId: number;
    open: boolean;
    onClose?: () => void;
  } = $props();

  // Show PDF directly if it exists, otherwise fall back to HTML preview
  let pdfUrl = $derived(`/api/invoices/${memberId}/download`);
</script>

{#if open}
  <dialog class="modal modal-open">
    <div class="modal-box w-11/12 max-w-5xl h-[80vh]">
      <iframe
        src={pdfUrl}
        class="w-full h-full border-0"
        title="Aperçu facture"
      ></iframe>
      <div class="modal-action">
        <button class="btn" onclick={() => onClose?.()}>Fermer</button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button onclick={() => onClose?.()}>close</button>
    </form>
  </dialog>
{/if}
