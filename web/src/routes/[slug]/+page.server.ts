import { error } from '@sveltejs/kit';
import { getStashApiV1StashesSlugGet } from '$lib/client';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params }) => {
	const slug = params.slug;

	const contentPromise = getStashApiV1StashesSlugGet({
		path: { slug }
	}).then((response) => {
		if (response.data === undefined || response.error) {
			const err = response.error.detail;
			return err;
		} // TODO: How TF do I get an error to throw here and be handled nicely by the page?
		return response.data;
	});

	return {
		slug,
		streamed: {
			content: contentPromise
		}
	};
};
