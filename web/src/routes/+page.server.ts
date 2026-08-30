import { listStashesApiV1StashesGet } from '$lib/client';
import type { PageServerLoad } from './$types';

const PAGE_SIZE = 10;

export const load: PageServerLoad = async ({ url, parent, request }) => {
	const requestedPage = Number(url.searchParams.get('page') ?? '1');
	const page = Number.isInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1;

	const { user } = await parent();
	const cookie = request.headers.get('cookie') ?? '';
	const take = page === 1 ? PAGE_SIZE + 1 : PAGE_SIZE;

	const stashesPromise = listStashesApiV1StashesGet({
		query: { page, take, show_revoked: user?.is_admin, show_expired: user?.is_admin }, 
		credentials: 'include', 
		headers: { cookie }
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
