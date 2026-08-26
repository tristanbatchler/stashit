<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import QRCode from '@castlenine/svelte-qrcode';

	let { data } = $props();
	let pageUrl = $derived(page.url.href)
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
		<p>{data.isBinary ? "Downloads" : "Views"}: {data.viewcount}</p>
		<p>Unique: {data.uniqueViewcount}</p>
	</footer>
</section>
