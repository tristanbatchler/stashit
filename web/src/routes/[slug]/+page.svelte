<script lang="ts">
	let { data } = $props();
</script>

<section >
	<header>
		<h5>{data.slug}</h5>
	</header>
	{#await data.streamed.response}
		<section aria-busy="true"></section>
	{:then response}
		{#if response.error}
			<p>Error: {response.error?.detail || response.error}</p>
		{:else}
			<pre>{response.content}</pre>
		{/if}
	{/await}
</section>
