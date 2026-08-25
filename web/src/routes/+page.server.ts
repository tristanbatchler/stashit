import { listStashesApiV1StashesGet } from '$lib/client';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
	const stashesPromise = listStashesApiV1StashesGet().then((response) => {
		return { error: response.error, content: response.data };
	});

	return {
		streamed: {
			stashes: stashesPromise
		}
	};
};
