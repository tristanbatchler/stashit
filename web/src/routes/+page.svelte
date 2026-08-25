<script lang="ts">
	import { resolve } from '$app/paths';

	let { data } = $props();
</script>

{#await data.streamed.stashes}
	<section aria-busy="true"></section>
{:then response}
	{#if response.error}
		<p>Error: {response.error?.detail || response.error}</p>
	{:else}
		<section>
			<ul>
				{#each response.content as stash (stash.id_)}
					<li>
						<a href={resolve('/[slug]', { slug: stash.slug })}>
							<strong>{stash.slug}</strong>
						</a>
						<small>{stash.added}</small>
					</li>
				{/each}
			</ul>
		</section>
	{/if}
{/await}
