<script lang="ts">
	import '@picocss/pico/css/pico.css';
	import { resolve } from '$app/paths';

	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<header class="container">
<nav>
  <ul>
    <li><a href="{resolve('/')}"><strong>Stash It!</strong></a></li>
  </ul>
  <ul>
    <li><a href={resolve('/stashes/new')}>New stash</a></li>
    <li><a href="#">About</a></li>
    <li><a href="#">Contact</a></li>
    <li><a href="/auth/google">Log in with Google</a></li>
  </ul>
</nav>
</header>
<main class="container">
	{@render children()}
</main>

