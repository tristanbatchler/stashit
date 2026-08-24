<script lang="ts">
	import { getStashes, type Stash } from '$lib/api';

	let stashes = $state<Stash[]>([]);
	let error = $state<string | null>(null);

	$effect(() => {
		getStashes()
			.then((value) => (stashes = value))
			.catch((reason: unknown) => {
				error = String(reason);
			});
	});
</script>

<h1>Stash It</h1>

{#if error}
	<p>{error}</p>
{:else}
	<ul>
		{#each stashes as stash}
			<li>
				<strong>{stash.slug}</strong>
				<small>{stash.added}</small>
			</li>
		{/each}
	</ul>
{/if}