<script lang="ts">
  import Navbar from './Navbar.svelte';
  import type { Snippet } from 'svelte';

  let { children }: { children?: Snippet } = $props();
</script>

<div class="min-h-screen">
  <Navbar />
  <main class="p-6">
    {@render children?.()}
  </main>
</div>
