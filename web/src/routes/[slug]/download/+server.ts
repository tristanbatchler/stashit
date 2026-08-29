import {
	getFileStashApiV1StashesFileSlugGet,
	unlockProtectedFileStashApiV1StashesFileSlugUnlockPost
} from '$lib/client';
import { error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

function getDownloadHeaders(response: Response): Headers {
	const headers = new Headers();

	const contentType = response.headers.get('content-type');
	if (contentType) headers.set('content-type', contentType);

	const contentDisposition = response.headers.get('content-disposition');
	if (contentDisposition) headers.set('content-disposition', contentDisposition);

	const contentLength = response.headers.get('content-length');
	if (contentLength) headers.set('content-length', contentLength);

	return headers;
}

export const GET: RequestHandler = async ({ params, request }) => {
	const cookie = request.headers.get('cookie') ?? '';

	const { data, error: fileError, response } =
		await getFileStashApiV1StashesFileSlugGet({
			path: { slug: params.slug },
			credentials: 'include',
			headers: { cookie },
			parseAs: 'stream'
		});

	if (fileError || !data || !response) {
		error(response?.status ?? 500, {
			message: 'Could not download file'
		});
	}

	return new Response(data, {
		status: response.status,
		headers: getDownloadHeaders(response)
	});
};

export const POST: RequestHandler = async ({ params, request }) => {
	const formData = await request.formData();
	const password = formData.get('password');

	if (typeof password !== 'string' || password.length === 0) {
		error(400, {
			message: 'Password is required'
		});
	}

	const cookie = request.headers.get('cookie') ?? '';

	const { data, error: unlockError, response } =
		await unlockProtectedFileStashApiV1StashesFileSlugUnlockPost({
			path: { slug: params.slug },
			query: { password },
			credentials: 'include',
			headers: { cookie },
			parseAs: 'stream'
		});

	if (unlockError || !data || !response) {
		error(response?.status ?? 500, {
			message: 'Could not download file'
		});
	}

	return new Response(data, {
		status: response.status,
		headers: getDownloadHeaders(response)
	});
};
