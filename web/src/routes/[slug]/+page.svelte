<script lang="ts">
	let { data } = $props();
</script>

<section >
	<header>
		<h5>{data.slug}</h5>
	</header>
	{#await data.streamed.content}
		<section aria-busy="true"></section>
	{:then content}
		<pre>{content}</pre>
	{:catch error}
		<p>Error: {error}</p>
	{/await}
</section>
