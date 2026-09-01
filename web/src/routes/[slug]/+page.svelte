<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import QRCode from '@castlenine/svelte-qrcode';
	import { refreshAll } from '$app/navigation';
	import hljs from 'highlight.js';

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
	let isRevoking = $state(false);
	let showRevokeModal = $state(false);

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

	function formatDate(dateStr: string | null | undefined): string {
		if (!dateStr) return 'Never';
		const date = new Date(dateStr);
		return isNaN(date.getTime()) ? dateStr : date.toLocaleString();
	}

	async function copyToClipboard() {
		try {
			await navigator.clipboard.writeText(activeContent);
			copyStatus = "Copied!";
			setTimeout(() => {
				copyStatus = "Copy";
			}, 2000);
		} catch (err) {
			alert(`Failed to copy content: ${err}`);
		}
	}

	async function revoke() {
		isRevoking = true;
		const { error } = await revokeStashApiV1StashesSlugDelete({
			path: { slug: data.slug },
			credentials: 'include'
		});

		isRevoking = false;
		showRevokeModal = false;

		if (error) {
			alert(`Error revoking stash: ${error.detail}`);
			return;
		}

		refreshAll();
	}
</script>

<article>
	<header class="stash-header">
		<kbd class="slug-badge">{data.slug}</kbd>
		<small><strong>{data.isBinary ? 'Binary File' : 'Text'}</strong></small>
		{#if data.metadata.is_protected}
			<mark>Password Protected</mark>
		{/if}
	</header>

	{#if isRevoked}
		<blockquote class="status-error">
			<strong>Stash Revoked:</strong> This content has been revoked and is no longer accessible.
		</blockquote>

	{:else if isExpired && !isAdmin}
		<blockquote class="status-error">
			<strong>Stash Expired:</strong> This content has reached its expiry limit.
		</blockquote>

	{:else}
		{#if needsPassword}
			<form method="POST" action={formAction} class="auth-form">
				<label>
					Password Required
					<input
						type="password"
						name="password"
						autocomplete="current-password"
						placeholder="Enter password to unlock"
						required
					/>
				</label>
				<button type="submit">{data.isBinary ? 'Download File' : 'Unlock Content'}</button>
				{#if unlockError}
					<small class="error-text">{unlockError}</small>
				{/if}
			</form>
		{/if}

		{#if data.isBinary && !needsPassword}
			<a href={resolve('/[slug]/download', { slug: data.slug })} role="button">
				Download File
			</a>
		{/if}

		{#if shouldShowText}
			<div class="code-container">
				<button 
					type="button" 
					class="secondary copy-btn" 
					onclick={copyToClipboard}
				>
					{copyStatus}
				</button>
				<pre id="stash-text-content" use:highlight={activeContent}></pre>
			</div>
		{/if}
	{/if}

	<!-- Admin Control Panel & Full Details (Includes Share QR & Standard Views) -->
	{#if isAdmin}
		<footer>
			<div class="admin-header">
				<h6>Admin Details</h6>
				{#if !isRevoked}
					<button type="button" class="danger-btn" onclick={() => (showRevokeModal = true)}>
						Revoke Stash
					</button>
				{/if}
			</div>

			<div class="grid">
				<div>
					<small>Created</small>
					<div>{formatDate(data.metadata.added)}</div>
				</div>
				<div>
					<small>Created By IP</small>
					 <div>
						<code>
							{#if data.metadata.added_by_ip}
								<a href={resolve("/ip/[ip_addr]", {ip_addr: data.metadata.added_by_ip})}>{data.metadata.added_by_ip}</a>
							{:else}
								N/A
							{/if}
					 	</code>
					</div>
				</div>
				<div>
					<small>Expires</small>
					<div>{formatDate(data.metadata.expires_at)}</div>
				</div>
				<div>
					<small>Protection</small>
					<div>{data.metadata.is_protected ? 'Password' : 'None'}</div>
				</div>
			</div>
			
			<div class="grid admin-stats">
				<div>
					<small>Revoked Status</small>
					<div>{data.metadata.revoked_at ? formatDate(data.metadata.revoked_at) : 'No'}</div>
				</div>
				<div>
					<small>Revoked By User ID</small>
					<div>{data.metadata.revoked_by_user_id ?? 'N/A'}</div>
				</div>
				<div>
					<small>{data.isBinary ? 'Downloads' : 'Views'}</small>
					<div>
						<strong>
							{data.isBinary 
								? (data.views ?? 'N/A') 
								: (data.views !== undefined ? data.views + 1 : 'N/A')}
						</strong> 
						<small>
							({data.isBinary 
								? (data.uniqueViews ?? 'N/A') 
								: (data.uniqueViews !== undefined ? data.uniqueViews + 1 : 'N/A')} unique)
						</small>
					</div>
				</div>
				<div>
					<small>Share Stash</small>
					<div class="qr-wrapper">
						<QRCode data={pageUrl} size={100} />
					</div>
				</div>
			</div>
		</footer>

	<!-- Standard User Footer Stats & Sharing -->
	{:else if !isRevoked && !isExpired}
		<footer>
			<div class="grid">
				<div>
					<small>Expires</small>
					<div><strong>{formatDate(data.metadata.expires_at)}</strong></div>
				</div>
				<div>
					<small>{data.isBinary ? 'Downloads' : 'Views'}</small>
					<div>
						<strong>
							{data.isBinary 
								? (data.views ?? 'N/A') 
								: (data.views !== undefined ? data.views + 1 : 'N/A')}
						</strong> 
						<small>
							({data.isBinary 
								? (data.uniqueViews ?? 'N/A') 
								: (data.uniqueViews !== undefined ? data.uniqueViews + 1 : 'N/A')} unique)
						</small>
					</div>
				</div>
				<div>
					<small>Share Stash</small>
					<div class="qr-wrapper">
						<QRCode data={pageUrl} size={120} />
					</div>
				</div>
			</div>
		</footer>
	{/if}
</article>

<dialog open={showRevokeModal}>
	<article>
		<header>
			<p><strong>Confirm Revocation</strong></p>
			<a href="#close" aria-label="Close" class="close" onclick={(e) => { e.preventDefault(); showRevokeModal = false; }}></a>
		</header>
		<p>
			Are you sure you want to revoke stash <strong>{data.slug}</strong>? This action cannot be undone, and the content will no longer be accessible.
		</p>
		<footer>
			<div class="modal-actions">
				<button type="button" class="secondary" onclick={() => (showRevokeModal = false)} disabled={isRevoking}>
					Cancel
				</button>
				<button type="button" class="danger-btn" aria-busy={isRevoking} disabled={isRevoking} onclick={revoke}>
					{isRevoking ? 'Revoking…' : 'Yes, Revoke Stash'}
				</button>
			</div>
		</footer>
	</article>
</dialog>