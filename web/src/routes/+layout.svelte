<script lang="ts">
	import '@picocss/pico/css/pico.css';
	import { resolve } from '$app/paths';

	import favicon from '$lib/assets/favicon.svg';

	let { children, data } = $props();

  async function logout() {
		await fetch(resolve('/auth/google/logout'), {
			method: 'POST'
		});

		location.href = resolve('/');
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<header class="container">
	<nav>
		<ul>
			<li><a href={resolve('/')}><strong>Stash It!</strong></a></li>
		</ul>

		<ul>
			<li><a href={resolve('/stashes/new')}>New stash</a></li>

			{#if data.user}
      <li>
        <button
          type="button"
          class="secondary"
          onclick={logout}
        >
          Log out {data.user.name}
        </button>
      </li>
    {:else}
      <li><a href={resolve('/auth/google')}>Log in</a></li>
    {/if}
		</ul>
	</nav>
</header>

<main class="container">
	{@render children()}
</main>