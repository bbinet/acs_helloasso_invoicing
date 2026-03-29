<script lang="ts">
  import { logout, refreshCampaigns } from '../lib/api';
  import { authenticated } from '../lib/stores';
  import Icon from '../lib/Icon.svelte';

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
      class="btn btn-ghost btn-sm"
      onclick={handleRefresh}
      disabled={refreshing}
      title="Rafraîchir depuis HelloAsso"
    >
      {#if refreshing}
        <span class="loading loading-spinner loading-sm"></span>
      {:else}
        <Icon name="refresh" />
      {/if}
      <span class="hidden sm:inline">Rafraîchir</span>
    </button>
    <button class="btn btn-ghost btn-sm" onclick={handleLogout}>
      <Icon name="logout" />
      <span class="hidden sm:inline">Déconnexion</span>
    </button>
  </div>
</div>
