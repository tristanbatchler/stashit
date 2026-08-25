import { listStashesApiV1StashesGet } from '$lib/client';
import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
	const { data, error } = await listStashesApiV1StashesGet();

	if (error || data === undefined) {
		throw new Error('Failed to load stashes');
	}

	return {
		stashes: data
	};
}