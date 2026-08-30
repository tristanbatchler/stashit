<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';

	let { data } = $props();

	function formatDateShort(isoString: string | null | undefined): string {
		if (!isoString) return '—';
		const date = new Date(isoString);
		if (isNaN(date.getTime())) return isoString;

		return new Intl.DateTimeFormat('en-AU', {
			day: 'numeric',
			month: 'short',
			year: 'numeric'
		}).format(date);
	}

	function formatDateFull(isoString: string | null | undefined): string {
		if (!isoString) return '';
		const date = new Date(isoString);
		if (isNaN(date.getTime())) return isoString;

		return new Intl.DateTimeFormat('en-AU', {
			dateStyle: 'medium',
			timeStyle: 'medium'
		}).format(date);
	}
</script>

{#await data.streamed.stashes}
	<section aria-busy="true">
		Loading stashes...
	</section>
{:then response}
	{#if response.error}
		<p class="error-msg">Error: {response.error?.detail || response.error}</p>
	{:else}
		{#if response.stashes.length === 0 && data.page > 1}
			{goto(resolve('/'))}
		{:else}
			<div class="overflow-auto">
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
									<a 
										href={resolve('/[slug]', { slug: stash.slug })} 
										class="slug-link"
									>
										{stash.slug}
									</a>
								</th>
								<td>{stash.is_binary ? 'File' : 'Text'}</td>
								<td>
									<span data-tooltip={formatDateFull(stash.added)}>
										{formatDateShort(stash.added)}
									</span>
								</td>
								<td><code>{stash.added_by_ip}</code></td>
								{#if data.user?.is_admin}
									<td>
										{#if stash.revoked_at}
											<span data-tooltip={formatDateFull(stash.revoked_at)}>
												{formatDateShort(stash.revoked_at)}
											</span>
										{:else}
											-
										{/if}
									</td>
									<td>
										{#if stash.expires_at}
											<span data-tooltip={formatDateFull(stash.expires_at)}>
												{formatDateShort(stash.expires_at)}
											</span>
										{:else}
											-
										{/if}
									</td>
								{/if}
							</tr>
						{:else}
							<tr>
								<td colspan={data.user?.is_admin ? 6 : 4}>No stashes yet.</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

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
							<a href={resolve(`/?page=${data.page + 1}`)}>Next</a>
						</li>
					{/if}
				</ul>
			</nav>
		{/if}
	{/if}
{/await}