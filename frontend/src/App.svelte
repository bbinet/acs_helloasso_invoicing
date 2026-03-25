<script lang="ts">
  import { onMount } from 'svelte';
  import Router, { push } from 'svelte-spa-router';
  import Login from './pages/Login.svelte';
  import Dashboard from './pages/Dashboard.svelte';
  import Members from './pages/Members.svelte';
  import { checkAuth } from './lib/api';
  import { authenticated } from './lib/stores';

  const routes = {
    '/login': Login,
    '/': Dashboard,
    '/members': Members,
  };

  let checking = $state(true);

  onMount(async () => {
    // Skip auth check if already on login page
    if (window.location.hash === '#/login') {
      checking = false;
      return;
    }
    try {
      await checkAuth();
      authenticated.set(true);
    } catch {
      authenticated.set(false);
      push('/login');
    } finally {
      checking = false;
    }
  });
</script>

{#if checking}
  <div class="min-h-screen flex items-center justify-center">
    <span class="loading loading-spinner loading-lg"></span>
  </div>
{:else}
  <Router {routes} />
{/if}
