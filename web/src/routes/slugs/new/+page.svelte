<script lang="ts">
	import { enhance } from '$app/forms';
	import type { PageProps } from './$types';

	let { form }: PageProps = $props();
</script>

<form method="POST" use:enhance>
	<label>
		Stash some text
		<textarea name="content" autocomplete="off" required></textarea>
	</label>
	<button type="submit">Stash it</button>
</form>

{#if form?.message}
	<p>{form.message}</p>
{/if}
