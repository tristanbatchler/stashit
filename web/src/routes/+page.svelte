<script lang="ts">
	import { getStashes, type Stash } from '$lib/api';
	import { resolve } from '$app/paths';


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

<p><a href={resolve('/slugs/new')}>Stash new text</a></p>

{#if error}
	<p>{error}</p>
{:else}
	<ul>
		{#each stashes as stash (stash.id_)}
			<li>
				 <a href={resolve('/[slug]', {slug: stash.slug})}>
					<strong>{stash.slug}</strong>
				</a>
				<small>{stash.added}</small>
			</li>
		{/each}
	</ul>
{/if}
