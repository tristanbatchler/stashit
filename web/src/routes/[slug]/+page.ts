import { error } from '@sveltejs/kit';
import { getStashApiV1StashesSlugGet } from '$lib/client';
import type { PageLoad } from './$types';

export const load: PageLoad = ({ params }) => {
	const slug = params.slug;

	// Fire the request immediately, but do NOT await it here so the page loads instantly
	const contentPromise = getStashApiV1StashesSlugGet({
		path: { slug }
	}).then((response) => {
		if (response.data === undefined || response.error) {
			error(404, 'Stash not found');
		}
		return response.data;
	});

	return {
		slug,
		streamed: {
			content: contentPromise
		}
	};
};
