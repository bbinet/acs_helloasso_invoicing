<script lang="ts">
  import Router from 'svelte-spa-router';
  import Login from './pages/Login.svelte';
  import Dashboard from './pages/Dashboard.svelte';
  import Members from './pages/Members.svelte';
  import Invoices from './pages/Invoices.svelte';
  import Summary from './pages/Summary.svelte';

  const routes = {
    '/login': Login,
    '/': Dashboard,
    '/members': Members,
    '/invoices': Invoices,
    '/summary': Summary,
  };
</script>

<Router {routes} />
