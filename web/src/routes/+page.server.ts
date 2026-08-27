import { listStashesApiV1StashesGet } from '$lib/client';
import type { PageServerLoad } from './$types';

const PAGE_SIZE = 10;

export const load: PageServerLoad = async ({ url }) => {
	const requestedPage = Number(url.searchParams.get('page') ?? '1');
	const page = Number.isInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1;

	// Fetch one extra item so we can tell whether a next page exists without
	// the API having to expose a total count.
	const stashesPromise = listStashesApiV1StashesGet({
		query: { page, take: PAGE_SIZE + 1 }
	}).then((response) => {
		const stashes = response.data ?? [];

		return {
			error: response.error,
			stashes: stashes.slice(0, PAGE_SIZE),
			hasNext: stashes.length > PAGE_SIZE
		};
	});

	return {
		page,
		streamed: {
			stashes: stashesPromise
		}
	};
};