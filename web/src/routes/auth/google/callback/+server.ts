import { error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { googleCallbackApiV1AuthGoogleCallbackGet } from '$lib/client';

export const GET: RequestHandler = async ({ url }) => {
	const code = url.searchParams.get('code');
	const state = url.searchParams.get('state');

	if (!code || !state) {
		error(400, 'Missing OAuth callback parameters');
	}

	const result = await googleCallbackApiV1AuthGoogleCallbackGet({
		query: { code, state },
		fetch: (input, init) =>
			globalThis.fetch(input, {
				...init,
				redirect: 'manual'
			})
	});

	const { response, error: callbackError } = result;

	if (!response) {
		error(500, 'Google login failed');
	}

	if (response.status !== 303) {
		error(
			response.status,
			callbackError && 'detail' in callbackError
				? String(callbackError.detail)
				: 'Google login failed'
		);
	}

	const location = response.headers.get('location');

	if (!location) {
		error(500, 'Google login did not return a redirect');
	}

	const headers = new Headers({
		location
	});

	const setCookie = response.headers.get('set-cookie');

	if (setCookie) {
		headers.set('set-cookie', setCookie);
	}

	return new Response(null, {
		status: 303,
		headers
	});
};