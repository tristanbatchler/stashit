import {
	getStashMetadataApiV1StashesMetadataSlugGet,
	getTextStashApiV1StashesTextSlugGet
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

	if (metadata.is_binary) {
		return {
			slug,
			isBinary: true as const
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
		content
	};
};