<script lang="ts">
	import { resolve } from '$app/paths';

	let { data } = $props();
</script>

{#await data.streamed.stashes}
	<section aria-busy="true"></section>
{:then stashes}
	<section>
		<ul>
			{#each stashes as stash (stash.id_)}
				<li>
					<a href={resolve('/[slug]', { slug: stash.slug })}>
						<strong>{stash.slug}</strong>
					</a>
					<small>{stash.added}</small>
				</li>
			{/each}
		</ul>
	</section>
{/await}
