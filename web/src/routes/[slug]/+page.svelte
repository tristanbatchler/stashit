<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import QRCode from '@castlenine/svelte-qrcode';

	let { data } = $props();
	let pageUrl = $derived(page.url.href);
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
