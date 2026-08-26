import { getFileStashApiV1StashesFileSlugGet } from '$lib/client';
import { error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ params }) => {
	const slug = params.slug;

	const { data, error: fileError, response } = await getFileStashApiV1StashesFileSlugGet({
		path: { slug },
		parseAs: 'stream'
	});

	if (fileError || !data || !response) {
		error(response?.status ?? 500, { message: 'Could not download file' });
	}

	const headers = new Headers();
	const contentType = response.headers.get('content-type');
	if (contentType) headers.set('content-type', contentType);
	const contentDisposition = response.headers.get('content-disposition');
	if (contentDisposition) headers.set('content-disposition', contentDisposition);
	const contentLength = response.headers.get('content-length');
	if (contentLength) headers.set('content-length', contentLength);

	// data is the body stream when parseAs: 'stream'
	return new Response(data, {
		status: 200,
		headers
	});
};