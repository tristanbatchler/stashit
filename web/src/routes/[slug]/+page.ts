import { error } from '@sveltejs/kit';
import { getStashApiV1StashesSlugGet } from '$lib/client';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({params}) => {
	const { data, error: responseError } = await getStashApiV1StashesSlugGet({
		path: {
			slug: params.slug
		}
	});

	if (responseError || data === undefined) {
		error(500, 'Failed to load stash');
	}

	return {
		content: data
	};
};