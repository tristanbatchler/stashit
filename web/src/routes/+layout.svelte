<script lang="ts">
	import '../app.scss';
	import { resolve } from '$app/paths';
	import favicon from '$lib/assets/favicon.svg';
	import { browser } from '$app/environment';

	let { children, data } = $props();

	let isDarkMode = $state(false);

	$effect(() => {
		if (!browser) return;
		
		const updateTheme = () => {
			const htmlTheme = document.documentElement.getAttribute('data-theme');
			if (htmlTheme) {
				isDarkMode = htmlTheme === 'dark';
			} else {
				isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
			}
		};

		updateTheme();

		const observer = new MutationObserver(updateTheme);
		observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
		
		const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
		mediaQuery.addEventListener('change', updateTheme);

		return () => {
			observer.disconnect();
			mediaQuery.removeEventListener('change', updateTheme);
		};
	});

	async function logout() {
		await fetch(resolve('/auth/google/logout'), { method: 'POST' });
		location.href = resolve('/');
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<!-- Dynamically switch the highlight.js theme stylesheet -->
	{#if isDarkMode}
		<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css" />
	{:else}
		<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css" />
	{/if}
</svelte:head>

<header class="app-header">
	<div class="container">
		<nav>
			<ul>
				<li>
					<a href={resolve('/')} class="brand-logo">
						<strong>Stash It!</strong>
					</a>
				</li>
			</ul>

			<ul>
				<li>
					<a href={resolve('/stashes/new')} class="nav-link">New stash</a>
				</li>

				{#if data.user}
					<li>
						<button
							type="button"
							class="outline nav-btn"
							onclick={logout}
						>
							Log out <span>{data.user.name}</span>
						</button>
					</li>
				{:else}
					<li>
						<a href={resolve('/auth/google')} role="button" class="nav-btn">Log in</a>
					</li>
				{/if}
			</ul>
		</nav>
	</div>
</header>

<main class="container app-main">
	{@render children()}
</main>