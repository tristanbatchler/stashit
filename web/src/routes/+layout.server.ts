import type { LayoutServerLoad } from './$types';
import { getMeApiV1AuthGoogleMeGet } from '$lib/client';

export const load: LayoutServerLoad = async ({ request }) => {
        const response = await getMeApiV1AuthGoogleMeGet({
                headers: {
                        Cookie: request.headers.get('cookie') ?? ''
                }
        });

        return {
                user: response?.data ?? null
        };
};