<script lang="ts">
  import { login } from '../lib/api';
  import { authenticated } from '../lib/stores';
  import { push } from 'svelte-spa-router';

  let password = $state('');
  let error = $state('');
  let submitting = $state(false);

  async function handleSubmit(e: Event) {
    e.preventDefault();
    error = '';
    submitting = true;
    try {
      await login(password);
      authenticated.set(true);
      push('/');
    } catch (err: any) {
      error = err.detail || 'Erreur de connexion';
    } finally {
      submitting = false;
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center bg-base-200">
  <div class="card w-96 bg-base-100 shadow-xl">
    <div class="card-body items-center text-center">
      <h2 class="card-title text-2xl mb-4">ACS Facturation</h2>
      <form onsubmit={handleSubmit} class="w-full">
        <div class="form-control">
          <input
            type="password"
            placeholder="Mot de passe"
            class="input input-bordered w-full"
            bind:value={password}
          />
        </div>
        {#if error}
          <div class="alert alert-error mt-4">
            <span>{error}</span>
          </div>
        {/if}
        <div class="card-actions mt-4 w-full">
          <button type="submit" class="btn btn-primary w-full" disabled={submitting}>
            Connexion
          </button>
        </div>
      </form>
    </div>
  </div>
</div>
