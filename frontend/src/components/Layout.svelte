<script lang="ts">
  import Sidebar from './Sidebar.svelte';
  import type { Snippet } from 'svelte';

  let { children }: { children?: Snippet } = $props();
</script>

<div class="drawer lg:drawer-open">
  <input id="app-drawer" type="checkbox" class="drawer-toggle" />

  <div class="drawer-content p-6">
    <label for="app-drawer" class="btn btn-ghost drawer-button lg:hidden">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </label>
    {@render children?.()}
  </div>

  <div class="drawer-side">
    <label for="app-drawer" aria-label="close sidebar" class="drawer-overlay"></label>
    <Sidebar />
  </div>
</div>
