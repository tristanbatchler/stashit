<script lang="ts">
	import { getTextStash } from '$lib/api';
	import { page } from '$app/state';

	let content = $state<string | null>(null);
	let error = $state<string | null>(null);

	$effect(() => {
		const slug = page.params.slug;

		if (!slug) {
			error = 'Missing slug in route parameters.';
			return;
		}

		// Reset state before loading the new slug.
		error = null;
		content = null;

		let cancelled = false;

		getTextStash(slug)
			.then((stash) => {
				if (!cancelled) {
					content = stash.content;
				}
			})
			.catch((reason: unknown) => {
				if (!cancelled) {
					error = String(reason);
				}
			});

		return () => {
			cancelled = true;
		};
	});
</script>

{#if error}
	<p>{error}</p>
{:else if content === null}
	<p>Loading...</p>
{:else}
	<pre>{content}</pre>
{/if}