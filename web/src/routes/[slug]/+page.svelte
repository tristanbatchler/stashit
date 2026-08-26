<script lang="ts">
	import { resolve } from '$app/paths';

	let { data } = $props();
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
</section>
