import { getStashApiV1StashesSlugGet } from '$lib/client';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params }) => {
	const slug = params.slug;

	const responsePromise = getStashApiV1StashesSlugGet({
		path: { slug }
	}).then((response) => {
		return { error: response.error, content: response.data };
	});

	return {
		slug,
		streamed: {
			response: responsePromise
		}
	};
};