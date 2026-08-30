<script lang="ts">
	import { resolve } from '$app/paths';
	import { createStash, type CreatedStash } from '$lib/stashes';

	let activeTab = $state<'text' | 'file'>('text');
	let text = $state('');
	let fileInput: HTMLInputElement | null = null;
	let selectedFileName = $state<string | null>(null);

	let hasExpiry = $state(false);
	let expiresAt = $state('');
	let password = $state('');

	let isSubmitting = $state(false);
	let progressPercent = $state<number | null>(null);
	let stash = $state<CreatedStash | null>(null);
	let error = $state<string | null>(null);

	function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files.length > 0) {
			selectedFileName = target.files[0].name;
		} else {
			selectedFileName = null;
		}
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
			if (fileInput) {
				fileInput.files = event.dataTransfer.files;
				selectedFileName = event.dataTransfer.files[0].name;
			}
		}
	}

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
	}

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();

		error = null;
		stash = null;
		progressPercent = null;
		isSubmitting = true;

		const file = activeTab === 'file' ? fileInput?.files?.[0] : undefined;
		const textPayload = activeTab === 'text' ? text : '';

		try {
			stash = await createStash(
				file,
				textPayload,
				hasExpiry ? new Date(expiresAt).toISOString() : undefined,
				password || undefined,
				(loaded, total) => {
					progressPercent = Math.round((loaded / total) * 100);
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

<article>
	<header>
		<div role="group">
			<button
				type="button"
				class={activeTab === 'text' ? '' : 'outline'}
				onclick={() => (activeTab = 'text')}
			>
				Text Snippet
			</button>
			<button
				type="button"
				class={activeTab === 'file' ? '' : 'outline'}
				onclick={() => (activeTab = 'file')}
			>
				Upload File
			</button>
		</div>
	</header>

	<form onsubmit={handleSubmit}>
		{#if activeTab === 'text'}
			<label>
				Content
				<textarea
					bind:value={text}
					placeholder="Paste your code or text here..."
					rows="10"
					autocomplete="off"
					class="code-input"
				></textarea>
			</label>
		{:else}
			<div 
				class="dropzone"
				ondrop={handleDrop}
				ondragover={handleDragOver}
				role="region"
				aria-label="File upload dropzone"
			>
				<input
					bind:this={fileInput}
					name="file"
					type="file"
					onchange={handleFileSelect}
					id="file-input-hidden"
				/>
				<label for="file-input-hidden" class="dropzone-label">
					{#if selectedFileName}
						<div>
							<span class="file-name">{selectedFileName}</span><br/>
							<small>Click to choose a different file</small>
						</div>
					{:else}
						<div>
							<span>Drag and drop a file here</span><br/>
							<small>or click to browse from your device</small>
						</div>
					{/if}
				</label>
			</div>
		{/if}

		<div class="settings-group">
			<label>
				Password Protection <small>(optional)</small>
				<input
					type="password"
					bind:value={password}
					placeholder="Optional password"
					autocomplete="new-password"
				/>
			</label>

			<div class="expiry-group">
				<label class="expiry-switch">
					<input type="checkbox" role="switch" bind:checked={hasExpiry} />
					<span>Set Expiry Date</span>
				</label>

				{#if hasExpiry}
					<label class="expiry-picker">
						Expires at
						<input
							type="datetime-local"
							bind:value={expiresAt}
							required
						/>
					</label>
				{/if}
			</div>
		</div>

		<button type="submit" class="submit-btn" aria-busy={isSubmitting} disabled={isSubmitting}>
			{isSubmitting ? 'Uploading…' : 'Stash It'}
		</button>
	</form>

	{#if isSubmitting && progressPercent !== null}
		<div class="progress-wrapper">
			<label for="upload-progress">
				Uploading stash: {progressPercent}%
			</label>
			<progress id="upload-progress" value={progressPercent} max="100"></progress>
		</div>
	{/if}

	{#if stash}
		<blockquote class="status-success">
			<h3>Your stash is ready</h3>
			<kbd>{stash.slug}</kbd>
			<div class="action-link">
				<a href={resolve('/[slug]', { slug: stash.slug })} role="button">
					View Stash →
				</a>
			</div>
		</blockquote>
	{/if}

	{#if error}
		<blockquote class="status-error">
			<strong>Error:</strong> {error}
		</blockquote>
	{/if}
</article>