<!-- web/src/routes/ip/[ip_addr]/+page.svelte -->
<script lang="ts">
	import { resolve } from '$app/paths';
	import { enhance } from '$app/forms';

	let { data, form } = $props();

	let hasPreviousPage = $derived(data.page > 1);
	let hasNextPage = $derived(data.activity.length === data.take);

	function formatDate(value: string | Date | null | undefined): string {
		if (!value) return 'Never';
		return new Date(value).toLocaleString();
	}
</script>

<svelte:head>
	<title>IP Activity — {data.ipAddress}</title>
</svelte:head>

<section>
	<header>
		<h1>{data.ipAddress}</h1>
	</header>

	{#if data.activeBan}
		<section>
			<h2>Active ban</h2>
			<dl>
				<dt>Added</dt>
				<dd>{formatDate(data.activeBan.added)}</dd>

				<dt>Expires</dt>
				<dd>{formatDate(data.activeBan.expires)}</dd>

				<dt>Reason</dt>
				<dd>{data.activeBan.reason ?? '—'}</dd>
			</dl>

			<form method="POST" action="?/revoke" use:enhance>
				<input type="hidden" name="ban_id" value={data.activeBan.id_} />

				<label>
					Revocation reason
					<textarea
						name="reason"
						rows="2"
						placeholder="Optional reason for lifting the ban"
					></textarea>
				</label>

				<button type="submit">Revoke ban</button>
			</form>

			{#if form?.revokeError}
				<p>{form.revokeError}</p>
			{/if}
			{#if form?.revokeSuccess}
				<p>Ban revoked successfully.</p>
			{/if}
		</section>
	{:else}
		<section>
			<h2>Ban IP address</h2>

			<form method="POST" action="?/ban" use:enhance>
				<label>
					Expiry
					<input type="datetime-local" name="expires" />
				</label>

				<label>
					Reason
					<textarea
						name="reason"
						rows="3"
						placeholder="Reason for banning this IP"
					></textarea>
				</label>

				<button type="submit">Ban IP</button>

				{#if form?.banError}
					<p>{form.banError}</p>
				{/if}
				{#if form?.banSuccess}
					<p>IP address banned successfully.</p>
				{/if}
			</form>
		</section>
	{/if}

	<section>
		<h2>IP activity</h2>

		{#if data.activity.length === 0}
			<p>No activity recorded for this IP address.</p>
		{:else}
			<table>
				<thead>
					<tr>
						<th>Time</th>
						<th>Type</th>
						<th>Stash</th>
						<th>Details</th>
					</tr>
				</thead>

				<tbody>
					{#each data.activity as activity, index (index)}
						<tr>
							<td>{formatDate(activity.event_at)}</td>
							<td>{activity.event_type}</td>
							<td>
								{#if activity.slug}
									<a href={resolve('/[slug]', { slug: activity.slug })}>
										{activity.slug}
									</a>
								{:else}
									—
								{/if}
							</td>
							<td>{activity.details ?? '—'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{/if}

		<nav aria-label="Activity pagination">
			{#if hasPreviousPage}
				<a href={resolve(`/ip/${data.ipAddress}?page=${data.page - 1}&take=${data.take}`)}>
					Previous
				</a>
			{/if}

			<span>Page {data.page}</span>

			{#if hasNextPage}
				<a href={resolve(`/ip/${data.ipAddress}?page=${data.page + 1}&take=${data.take}`)}>
					Next
				</a>
			{/if}
		</nav>
	</section>
</section>