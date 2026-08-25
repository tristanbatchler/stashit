<script lang="ts">
	let { data } = $props();
</script>

{#await data.streamed.content}
	<article aria-busy="true"></article>
{:then content}
	<article>
		<header>
			<h5>{data.slug}</h5>
		</header>
		<pre>{content}</pre>
	</article>
{/await}
