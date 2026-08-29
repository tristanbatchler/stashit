import {
	getStashMetadataApiV1StashesMetadataSlugGet,
	getStashViewsApiV1StashesViewsSlugGet,
	getTextStashApiV1StashesTextSlugGet
} from '$lib/client';
import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, parent, request }) => {
	const { slug } = params;
	const { user } = await parent();
	const cookie = request.headers.get('cookie') ?? '';

	const { data: metadata, error: metadataError } =
		await getStashMetadataApiV1StashesMetadataSlugGet({
			path: { slug }
		});

	if (metadataError || !metadata) {
		error(404, {
			message:
				metadataError && 'detail' in metadataError
					? String(metadataError.detail)
					: 'Could not load stash'
		});
	}

	const [{ data: views }, { data: uniqueViews }] = await Promise.all([
		getStashViewsApiV1StashesViewsSlugGet({
			path: { slug },
			query: { unique: false },

		}),
		getStashViewsApiV1StashesViewsSlugGet({
			path: { slug },
			query: { unique: true },
		})
	]);

	const result = {
		slug,
		user,
		metadata,
		isBinary: metadata.is_binary,
		views,
		uniqueViews
	};

	if (metadata.revoked_at || metadata.is_binary) {
		return result;
	}

	const { data: content, error: contentError } =
		await getTextStashApiV1StashesTextSlugGet({
			path: { slug },
			credentials: 'include',
			headers: { cookie }
		});

	if (contentError || content === undefined) {
		error(500, {
			message:
				contentError && 'detail' in contentError
					? String(contentError.detail)
					: 'Could not load text content'
		});
	}

	return {
		...result,
		content
	};
};