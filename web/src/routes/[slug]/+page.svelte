<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import QRCode from '@castlenine/svelte-qrcode';

	import {revokeStashApiV1StashesSlugDelete} from '$lib/client'
	import { refreshAll } from '$app/navigation';

	let { data } = $props();
	let pageUrl = $derived(page.url.href);

	async function revoke() {
		const { error } = await revokeStashApiV1StashesSlugDelete(
			{path: {slug: data.slug}, credentials: 'include'}
		);

		if (error) {
			alert(`Error revoking stash: ${error.detail}`)
		}

		refreshAll();
	}
</script>

<section>
	<header>
		<h5>{data.slug}</h5>
	</header>

	{#if data.isBinary}
		<p>
			<a href={resolve('/[slug]/download', {slug: data.slug})}>Download file</a>
		</p>
	{:else}
		<pre>{data.content}</pre>
	{/if}

	<section>
		<h6>Share</h6>
		<QRCode data={pageUrl} />
	</section>

	{#if data.user?.is_admin}
		<section>
			<button type="button" onclick={revoke}>
				Revoke
			</button>
		</section>
	{/if}

	<footer>
		{#if data.isBinary}
			<p>Downloads: {data.views ?? "N/A"}</p>
			<p>Unique: {data.uniqueViews ?? "N/A"}</p>
		{:else}
			<p>Views: {data.views !== undefined ? data.views + 1 : "N/A"}</p>
			<p>Unique: {data.uniqueViews == 0 ? 1 : data.uniqueViews ?? "N/A"}</p>
		{/if}
	</footer>
</section>
