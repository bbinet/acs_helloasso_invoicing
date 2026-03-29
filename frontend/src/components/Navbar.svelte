<script lang="ts">
  import { logout, refreshCampaigns } from '../lib/api';
  import { authenticated } from '../lib/stores';

  let refreshing = $state(false);

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // ignore
    }
    authenticated.set(false);
    window.location.hash = '#/login';
  }

  async function handleRefresh() {
    refreshing = true;
    try {
      await refreshCampaigns();
      window.dispatchEvent(new CustomEvent('helloasso-refreshed'));
    } finally {
      refreshing = false;
    }
  }

  let currentHash = $state(window.location.hash || '#/');

  function isActive(path: string) {
    return currentHash === `#${path}`;
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('hashchange', () => {
      currentHash = window.location.hash || '#/';
    });
  }
</script>

<div class="navbar bg-base-200 px-4">
  <div class="flex-1 gap-2">
    <a
      class="btn btn-sm {isActive('/') ? 'btn-primary' : 'btn-ghost'}"
      href="#/"
    >
      Dashboard
    </a>
    <a
      class="btn btn-sm {isActive('/members') ? 'btn-primary' : 'btn-ghost'}"
      href="#/members"
    >
      Membres
    </a>
    <a
      class="btn btn-sm {isActive('/graphs') ? 'btn-primary' : 'btn-ghost'}"
      href="#/graphs"
    >
      Graphiques
    </a>
  </div>
  <div class="flex-none gap-2 flex items-center">
    <button
      class="btn btn-outline btn-sm"
      onclick={handleRefresh}
      disabled={refreshing}
      title="Rafraîchir depuis HelloAsso"
    >
      {#if refreshing}
        <span class="loading loading-spinner loading-sm"></span>
      {:else}
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      {/if}
      <span class="hidden sm:inline">Rafraîchir</span>
    </button>
    <button class="btn btn-ghost btn-sm" onclick={handleLogout}>
      Déconnexion
    </button>
  </div>
</div>
