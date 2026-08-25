import { error } from '@sveltejs/kit';
import { listStashesApiV1StashesGet } from '$lib/client';
import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
	const { data, error: responseError } = await listStashesApiV1StashesGet();

	if (data === undefined || responseError) {
		error(500, 'Failed to load stashes');
	}

	return {
		stashes: data
	};
}