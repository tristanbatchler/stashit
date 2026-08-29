import {
	getStashMetadataApiV1StashesMetadataSlugGet,
	getStashViewsApiV1StashesViewsSlugGet,
	getTextStashApiV1StashesTextSlugGet
} from '$lib/client';
import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, parent }) => {
	const { slug } = params;
	const { user } = await parent();

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

	const [{ data: views }, { data: uniqueViews }] = await Promise.all([
		getStashViewsApiV1StashesViewsSlugGet({
			path: { slug },
			query: { unique: false }
		}),
		getStashViewsApiV1StashesViewsSlugGet({
			path: { slug },
			query: { unique: true }
		})
	]);

	if (metadata.revoked_at) {
		return {
			slug,
			user,
			metadata,
			isBinary: metadata.is_binary,
			views,
			uniqueViews
		};
	}

	if (metadata.is_binary) {
		return {
			slug,
			user,
			metadata,
			isBinary: true as const,
			views,
			uniqueViews
		};
	}

	const { data: content, error: textError } =
		await getTextStashApiV1StashesTextSlugGet({
			path: { slug }
		});

	if (textError || content === undefined || content === null) {
		error(500, {
			message:
				textError && typeof textError === 'object' && 'detail' in textError
					? String(textError.detail)
					: 'Could not load text content'
		});
	}

	return {
		slug,
		user,
		metadata,
		isBinary: false as const,
		content,
		views,
		uniqueViews
	};
};