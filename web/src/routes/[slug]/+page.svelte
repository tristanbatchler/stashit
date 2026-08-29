<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import QRCode from '@castlenine/svelte-qrcode';
	import { refreshAll } from '$app/navigation';

	import { revokeStashApiV1StashesSlugDelete } from '$lib/client';

	let { data } = $props();

	let pageUrl = $derived(page.url.href);
	let isAdmin = $derived(data.user?.is_admin ?? false);
	let isRevoked = $derived(data.metadata.revoked_at !== null);

	async function revoke() {
		const { error } = await revokeStashApiV1StashesSlugDelete({
			path: { slug: data.slug },
			credentials: 'include'
		});

		if (error) {
			alert(`Error revoking stash: ${error.detail}`);
			return;
		}

		refreshAll();
	}
</script>

<section>
	<header>
		<h5>{data.slug}</h5>
	</header>

	{#if isAdmin}
		{#if isRevoked}
			<p>This stash has been revoked.</p>
		{:else if data.isBinary}
			<p>
				<a href={resolve('/[slug]/download', { slug: data.slug })}>
					Download file
				</a>
			</p>
		{:else}
			<pre>{data.content}</pre>
		{/if}

		<section>
			<h6>Metadata</h6>

			<dl>
				<dt>Created</dt>
				<dd>{data.metadata.added ?? 'N/A'}</dd>

				<dt>Created by</dt>
				<dd>{data.metadata.added_by_ip ?? 'N/A'}</dd>

				<dt>Expires</dt>
				<dd>{data.metadata.expires_at ?? 'Never'}</dd>

				<dt>Type</dt>
				<dd>{data.isBinary ? 'Binary' : 'Text'}</dd>

				<dt>Revoked</dt>
				<dd>{data.metadata.revoked_at ?? 'No'}</dd>

				<dt>Revoked by</dt>
				<dd>{data.metadata.revoked_by_user_id ?? 'N/A'}</dd>

				{#if data.isBinary}
					<dt>Downloads</dt>
					<dd>{data.views ?? 'N/A'}</dd>

					<dt>Unique downloads</dt>
					<dd>{data.uniqueViews ?? 'N/A'}</dd>
				{:else}
					<dt>Views</dt>
					<dd>{data.views ?? 'N/A'}</dd>

					<dt>Unique views</dt>
					<dd>{data.uniqueViews ?? 'N/A'}</dd>
				{/if}
			</dl>
		</section>

		{#if !isRevoked}
			<section>
				<button type="button" onclick={revoke}>
					Revoke
				</button>
			</section>
		{/if}

	{:else if isRevoked}
		<p>This stash has been revoked.</p>

	{:else}
		{#if data.isBinary}
			<p>
				<a href={resolve('/[slug]/download', { slug: data.slug })}>
					Download file
				</a>
			</p>
		{:else}
			<pre>{data.content}</pre>
		{/if}

		<p>
			<strong>Expires:</strong> {data.metadata.expires_at ?? 'Never'}
		</p>

		<section>
			<h6>Share</h6>
			<QRCode data={pageUrl} />
		</section>

		<footer>
			{#if data.isBinary}
				<p>Downloads: {data.views ?? 'N/A'}</p>
				<p>Unique downloads: {data.uniqueViews ?? 'N/A'}</p>
			{:else}
				<p>
					Views: {data.views !== undefined
						? data.views + 1
						: 'N/A'}
				</p>
				<p>
					Unique views: {data.uniqueViews !== undefined
						? data.uniqueViews + 1
						: 'N/A'}
				</p>
			{/if}
		</footer>
	{/if}
</section>
