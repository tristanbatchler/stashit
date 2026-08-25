<script lang="ts">
	import { enhance } from '$app/forms';
	import type { PageProps } from './$types';

	let { form }: PageProps = $props();
	
	// Local state to track when the form is actively submitting
	let isSubmitting = $state(false);
</script>

<form 
	method="POST" 
	use:enhance={() => {
		isSubmitting = true;
		
		return async ({ update }) => {
			await update();
			isSubmitting = false;
		};
	}}
>
	<fieldset>
		<label>
			Stash some text
			<textarea name="content" autocomplete="off" required></textarea>
		</label>
	</fieldset>
	
	<button type="submit" aria-busy={isSubmitting} disabled={isSubmitting}>
		{#if isSubmitting}
			<span>Generating your link...</span>
		{:else}
			Stash it
		{/if}
	</button>
</form>

{#if form?.message}
	<p>{form.message}</p>
{/if}
