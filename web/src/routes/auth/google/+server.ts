import { redirect } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { googleLoginApiV1AuthGoogleGet } from '$lib/client';

export const GET: RequestHandler = async () => {
	const { data: googleRedirect, error } = await googleLoginApiV1AuthGoogleGet();

	if (!googleRedirect || error) {
		throw new Error(`Google login response did not contain a URL: ${error.detail}`);
	}
	throw redirect(302, googleRedirect.url);
};