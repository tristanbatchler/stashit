import { createClient, type Client } from '$lib/client/client';
import { xhrFetch } from '$lib/xhr-fetch';

export function createUploadClient(
	onProgress: (loaded: number, total: number) => void
): Client {
	return createClient({
		fetch: xhrFetch(onProgress)
	});
}