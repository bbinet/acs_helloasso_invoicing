<script lang="ts">
  import { logout } from '../lib/api';
  import { authenticated } from '../lib/stores';

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // ignore
    }
    authenticated.set(false);
    window.location.hash = '#/login';
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

<div class="navbar bg-base-100 shadow-sm px-4">
  <div class="flex-1">
    <div role="tablist" class="tabs tabs-boxed">
      <a role="tab" class="tab" class:tab-active={isActive('/')} href="#/">
        Dashboard
      </a>
      <a role="tab" class="tab" class:tab-active={isActive('/members')} href="#/members">
        Membres
      </a>
    </div>
  </div>
  <div class="flex-none">
    <button class="btn btn-ghost btn-sm" onclick={handleLogout}>
      Déconnexion
    </button>
  </div>
</div>
