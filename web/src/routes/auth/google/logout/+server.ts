import { redirect } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { googleLogoutApiV1AuthGoogleLogoutPost } from '$lib/client';
import { resolve } from '$app/paths';

export const POST: RequestHandler = async ({ cookies }) => {
	const { error } = await googleLogoutApiV1AuthGoogleLogoutPost();

	if (error) {
		throw new Error(`Google logout error: ${error.detail}`);
	}

	cookies.delete('session', {
		path: '/'
	});

	throw redirect(303, resolve('/'));
};