<script lang="ts">
	import { resolve } from '$app/paths';

	let { data } = $props();
</script>

<h1>Stash It</h1>

<p><a href={resolve('/slugs/new')}>Stash new text</a></p>

<ul>
	{#each data.stashes as stash (stash.id_)}
		<li>
			<a href={resolve('/[slug]', { slug: stash.slug })}>
				<strong>{stash.slug}</strong>
			</a>
			<small>{stash.added}</small>
		</li>
	{/each}
</ul>