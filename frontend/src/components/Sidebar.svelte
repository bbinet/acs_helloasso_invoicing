<script lang="ts">
  import { logout } from '../lib/api';
  import { authenticated } from '../lib/stores';

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // ignore errors
    }
    authenticated.set(false);
    window.location.hash = '#/login';
  }
</script>

<ul class="menu bg-base-200 text-base-content min-h-full w-64 p-4">
  <li class="menu-title text-lg font-bold">ACS Facturation</li>
  <li><a href="#/">Dashboard</a></li>
  <li><a href="#/members">Membres</a></li>
  <li><a href="#/invoices">Factures</a></li>
  <li><a href="#/summary">Résumé</a></li>
  <li class="mt-auto">
    <button onclick={handleLogout} class="btn btn-ghost">Déconnexion</button>
  </li>
</ul>
