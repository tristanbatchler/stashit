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

		getTextStash(slug)
			.then((c) => {
				content = c;
			})
			.catch((reason: unknown) => {
				error = String(reason);
			});
	});
</script>

{#if error}
	<p>{error}</p>
{:else}
	<pre>{content}</pre>
{/if}
