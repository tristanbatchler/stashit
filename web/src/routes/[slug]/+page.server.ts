import {
	getStashMetadataApiV1StashesMetadataSlugGet,
	getTextStashApiV1StashesTextSlugGet,
	getStashViewsApiV1StashesViewsSlugGet,
} from '$lib/client';
import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params }) => {
	const slug = params.slug;

	const { data: metadata, error: metaError } =
		await getStashMetadataApiV1StashesMetadataSlugGet({
			path: { slug }
		});

	if (metaError || !metadata) {
		error(404, {
			message:
				metaError && typeof metaError === 'object' && 'detail' in metaError
					? String(metaError.detail)
					: 'Could not load stash'
		});
	}

	const { data: views  } = await getStashViewsApiV1StashesViewsSlugGet({
		path: {slug}, query: {unique: false}
	});

	const viewcount = views === undefined ? "N/A" : String(views);

	const { data: uniqueViews  } = await getStashViewsApiV1StashesViewsSlugGet({
		path: {slug}, query: {unique: true}
	});

	const uniqueViewcount = uniqueViews === undefined ? "N/A" : String(uniqueViews);

	if (metadata.is_binary) {
		return {
			slug,
			isBinary: true as const,
			viewcount,
			uniqueViewcount
		};
	}

	const { data: content, error: textError } = await getTextStashApiV1StashesTextSlugGet({
		path: { slug }
	});

	if (textError || content === undefined || content === null) {
		error(500, { message: 'Could not load text content' });
	}

	return {
		slug,
		isBinary: false as const,
		content,
		viewcount,
		uniqueViewcount
	};
};