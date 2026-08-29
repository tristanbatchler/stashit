<script lang="ts">
	import '@picocss/pico/css/pico.css';
	import { resolve } from '$app/paths';

	import favicon from '$lib/assets/favicon.svg';

	let { children, data } = $props();
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
          <form method="POST" action={resolve('/auth/google/logout')}>
            <button type="submit" class="secondary">
              Log out {data.user.name}
            </button>
          </form>
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