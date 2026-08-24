import { fail, redirect } from '@sveltejs/kit';
import type { Actions } from './$types';
import { postTextStash } from '$lib/api';

export const actions: Actions = {
	default: async ({ request }) => {
		const data = await request.formData();
		const content = data.get('content');

		if (typeof content !== 'string' || content.trim() === '') {
			return fail(400, { content, message: 'You have to type something to stash it.' });
		}

		const stash = await postTextStash(content).catch((reason: unknown) => {
			console.error('Failed to create text stash:', reason);
			return null;
		});

		if (!stash) {
			return fail(500, { content, message: 'Could not create the stash. Please try again.' });
		}

		throw redirect(303, `/${stash.slug}`);
	}
};
