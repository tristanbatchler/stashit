<script lang="ts">
	import { resolve } from '$app/paths';
	import { createStash, type CreatedStash } from '$lib/stashes';

	let text = $state('');
	let fileInput: HTMLInputElement | null = null;

	let isSubmitting = $state(false);
	let progressPercent = $state<number | null>(null);
	let stash = $state<CreatedStash | null>(null);
	let error = $state<string | null>(null);

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();

		error = null;
		stash = null;
		progressPercent = null;
		isSubmitting = true;

		const file = fileInput?.files?.[0];

		try {
			stash = await createStash(
				file,
				text,
				(loaded, total) => {
					progressPercent = Math.round(
						(loaded / total) * 100,
					);
				},
			);
		} catch (err) {
			error = err instanceof Error
				? err.message
				: String(err);
		} finally {
			isSubmitting = false;
		}
	}
</script>

<form onsubmit={handleSubmit}>
	<fieldset>
		<label>
			Stash some text
			<textarea bind:value={text} autocomplete="off"></textarea>
		</label>
	</fieldset>

	<fieldset>
		<label>
			Or a file...
			<input bind:this={fileInput} name="file" type="file" />
		</label>
	</fieldset>

	<button type="submit" aria-busy={isSubmitting} disabled={isSubmitting}>
		{isSubmitting ? 'Uploading…' : 'Stash it'}
	</button>
</form>

{#if isSubmitting && progressPercent !== null}
	<div>
		<label for="upload-progress">
			Upload progress: {progressPercent}%
		</label>

		<progress
			id="upload-progress"
			value={progressPercent}
			max="100"
		>
			{progressPercent}%
		</progress>
	</div>
{/if}

{#if stash}
	<section>
		<h3>Your stash is ready</h3>
		<p>{stash.slug}</p>

		<div>
			<a href={resolve('/[slug]', { slug: stash.slug })}>
				View stash →
			</a>
		</div>
	</section>
{/if}

{#if error}
	<p class="error">{error}</p>
{/if}