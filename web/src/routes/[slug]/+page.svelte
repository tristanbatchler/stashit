<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import QRCode from '@castlenine/svelte-qrcode';
	import { refreshAll } from '$app/navigation';
	import hljs from 'highlight.js';
	import 'highlight.js/styles/github.min.css'

	import { revokeStashApiV1StashesSlugDelete } from '$lib/client';

	let { data, form } = $props();

	let pageUrl = $derived(page.url.href);
	let isAdmin = $derived(data.user?.is_admin ?? false);
	let isRevoked = $derived(data.metadata.revoked_at !== null);
	let isExpired = $derived(
		data.metadata.expires_at !== null &&
			new Date(data.metadata.expires_at) <= new Date()
	);
	let unlockedContent = $derived(form?.unlockedContent);
	let unlockError = $derived(form?.unlockError);

	let activeContent = $derived(unlockedContent ?? data.content ?? "");

	let shouldShowText = $derived(
		!data.isBinary && 
		(isAdmin || !data.metadata.is_protected || unlockedContent !== undefined)
	);

	let needsPassword = $derived(
		data.metadata.is_protected && 
		!isAdmin && 
		(data.isBinary || unlockedContent === undefined)
	);

	let formAction = $derived(
		data.isBinary 
			? resolve('/[slug]/download', { slug: data.slug }) 
			: '?/unlock'
	);

	let copyStatus = $state("Copy");

	function highlight(node: HTMLElement, content: string) {
		function update(text: string) {
			node.textContent = text;
			hljs.highlightElement(node);
		}

		update(content);

		return {
			update
		};
	}

	async function copyToClipboard() {
		try {
			await navigator.clipboard.writeText(activeContent);
			copyStatus = "Copied!";
			setTimeout(() => {
				copyStatus = "Copy";
			}, 2000);
		} catch (err) {
			alert("Failed to copy text layout content.");
		}
	}

	async function revoke() {
		const { error } = await revokeStashApiV1StashesSlugDelete({
			path: { slug: data.slug },
			credentials: 'include'
		});

		if (error) {
			alert(`Error revoking stash: ${error.detail}`);
			return;
		}

		refreshAll();
	}
</script>

<header>
	<h5>{data.slug}</h5>
</header>

<article>
	<section>
		{#if isRevoked}
			<p>This stash has been revoked.</p>

		{:else if isExpired && !isAdmin}
			<p>This stash has expired.</p>

		{:else}
			{#if needsPassword}
				<form method="POST" action={formAction}>
					<label>
						Password
						<input
							type="password"
							name="password"
							autocomplete="current-password"
							required
						/>
					</label>

					<button type="submit">
						{data.isBinary ? 'Download' : 'Unlock'}
					</button>

					{#if unlockError}
						<p>{unlockError}</p>
					{/if}
				</form>
			{/if}

			{#if data.isBinary && !needsPassword}
				<p>
					<a href={resolve('/[slug]/download', { slug: data.slug })}>
						Download file
					</a>
				</p>
			{/if}

			{#if shouldShowText}
				<!-- 💡 Wrapped inside a styled layout wrapper container block -->
				<div class="code-container">
					<button 
						type="button" 
						class="copy-btn secondary outline" 
						onclick={copyToClipboard}
					>
						{copyStatus}
					</button>
					<pre id="stash-text-content" use:highlight={activeContent}></pre>
				</div>
			{/if}
		{/if}

		{#if isAdmin}
			<section>
				<h6>Metadata</h6>

				<dl>
					<dt>Created</dt>
					<dd>{data.metadata.added ?? 'N/A'}</dd>

					<dt>Created by</dt>
					<dd>{data.metadata.added_by_ip ?? 'N/A'}</dd>

					<dt>Expires</dt>
					<dd>{data.metadata.expires_at ?? 'Never'}</dd>

					<dt>Type</dt>
					<dd>{data.isBinary ? 'Binary' : 'Text'}</dd>

					<dt>Revoked</dt>
					<dd>{data.metadata.revoked_at ?? 'No'}</dd>

					<dt>Revoked by</dt>
					<dd>{data.metadata.revoked_by_user_id ?? 'N/A'}</dd>

					<dt>Protection</dt>
					<dd>
						{data.metadata.is_protected
							? 'Password protected'
							: 'None'}
					</dd>

					{#if data.isBinary}
						<dt>Downloads</dt>
						<dd>{data.views ?? 'N/A'}</dd>

						<dt>Unique downloads</dt>
						<dd>{data.uniqueViews ?? 'N/A'}</dd>
					{:else}
						<dt>Views</dt>
						<dd>{data.views ?? 'N/A'}</dd>

						<dt>Unique views</dt>
						<dd>{data.uniqueViews ?? 'N/A'}</dd>
					{/if}
				</dl>
			</section>

			{#if !isRevoked}
				<section>
					<button type="button" onclick={revoke}>
						Revoke
					</button>
				</section>
			{/if}

		{:else if !isRevoked && !isExpired}
			<p>
				<strong>Expires:</strong>
				{data.metadata.expires_at ?? 'Never'}
			</p>

			<section>
				<h6>Share</h6>
				<QRCode data={pageUrl} />
			</section>

			<footer>
				{#if data.isBinary}
					<p>Downloads: {data.views ?? 'N/A'}</p>
					<p>Unique downloads: {data.uniqueViews ?? 'N/A'}</p>
				{:else}
					<p>
						Views: {data.views !== undefined
							? data.views + 1
							: 'N/A'}
					</p>
					<p>
						Unique views: {data.uniqueViews !== undefined
							? data.uniqueViews + 1
							: 'N/A'}
					</p>
				{/if}
			</footer>
		{/if}
	</section>
</article>
