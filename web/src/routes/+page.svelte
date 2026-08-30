<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';

	let { data } = $props();
</script>

{#await data.streamed.stashes}
	<section aria-busy="true">
		Loading stashes...
	</section>
{:then response}
	{#if response.error}
		<p>Error: {response.error?.detail || response.error}</p>
	{:else}
		{#if response.stashes.length === 0 && data.page > 1}
			{goto(resolve('/'))}
		{:else}
			<table>
				<thead>
					<tr>
						<th scope="col">Unique ID</th>
						<th scope="col">Type</th>
						<th scope="col">Added</th>
						<th scope="col">IP</th>
						{#if data.user?.is_admin}
							<th scope="col">Revoked</th>
							<th scope="col">Expires</th>
						{/if}
					</tr>
				</thead>
				<tbody>
					{#each response.stashes as stash (stash.id_)}
						<tr>
							<th scope="row">
								<a href={resolve('/[slug]', { slug: stash.slug })}>{stash.slug}</a>
							</th>
							<td>{stash.is_binary ? 'File' : 'Text'}</td>
							<td>{stash.added}</td>
							<td>{stash.added_by_ip}</td>
							{#if data.user?.is_admin}
								<td>{stash.revoked_at}</td>
								<td>{stash.expires_at}</td>
							{/if}
						</tr>
					{:else}
						<tr>
							<td colspan="4">No stashes yet.</td>
						</tr>
					{/each}
				</tbody>
			</table>

			<nav aria-label="Pagination">
				<ul>
					{#if data.page > 1}
						<li>
							<a href={resolve(`/?page=${data.page - 1}`)}>Previous</a>
						</li>
					{/if}
					<li><span>Page {data.page}</span></li>
					{#if response.hasNext}
						<li>
							<a href={resolve(`/?page=${data.page + 1}`)}>Nek</a>
						</li>
					{/if}
				</ul>
			</nav>
		{/if}
	{/if}
{/await}
