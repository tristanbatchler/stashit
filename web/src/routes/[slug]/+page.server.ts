import {
	getStashMetadataApiV1StashesMetadataSlugGet,
	getStashViewsApiV1StashesViewsSlugGet,
	getTextStashApiV1StashesTextSlugGet,
	unlockProtectedTextStashApiV1StashesTextSlugUnlockPost
} from '$lib/client';
import { error, fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

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
			query: { unique: false }
		}),
		getStashViewsApiV1StashesViewsSlugGet({
			path: { slug },
			query: { unique: true }
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

	if (
		metadata.revoked_at ||
		metadata.is_binary ||
		(metadata.is_protected && !user?.is_admin)
	) {
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

export const actions: Actions = {
	unlock: async ({ params, request, cookies }) => {
		const formData = await request.formData();
		const password = formData.get('password');

		if (typeof password !== 'string' || password.length === 0) {
			return fail(400, {
				unlockError: 'Password is required'
			});
		}

		const cookie = cookies.toString();

		const { data: content, error: unlockError } =
			await unlockProtectedTextStashApiV1StashesTextSlugUnlockPost({
				path: {
					slug: params.slug
				},
				query: {
					password
				},
				credentials: 'include',
				headers: {
					cookie
				}
			});

		if (unlockError || content === undefined) {
			return fail(400, {
				unlockError:
					unlockError && 'detail' in unlockError
						? String(unlockError.detail)
						: 'Could not unlock stash'
			});
		}

		return {
			unlockedContent: content
		};
	}
};
