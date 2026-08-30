import type { LayoutServerLoad } from './$types';
import { getMeApiV1AuthGoogleMeGet } from '$lib/client';

export const load: LayoutServerLoad = async ({ request }) => {
	const { data: user, error } = await getMeApiV1AuthGoogleMeGet({
		headers: {
			Cookie: request.headers.get('cookie') ?? ''
		}
	});

	if (error) {
		console.log("Could not get response from getMeApiV1AuthGoogleMeGet - user will remain null");
	}

	return {
		user
	};
};