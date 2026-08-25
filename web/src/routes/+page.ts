import { error } from '@sveltejs/kit';
import { listStashesApiV1StashesGet } from '$lib/client';
import type { PageLoad } from './$types';

export const load: PageLoad = () => {
	const stashesPromise = listStashesApiV1StashesGet().then((response) => {
		if (response.data === undefined || response.error) {
			error(500, 'Failed to load stashes');
		}
		return response.data;
	});

	return {
		streamed: {
			stashes: stashesPromise
		}
	};
};
