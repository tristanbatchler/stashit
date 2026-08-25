import { fail, redirect } from '@sveltejs/kit';
import type { Actions } from './$types';
import { addTextStashApiV1StashesTextPost } from '$lib/client';
import { resolve } from '$app/paths';

export const actions: Actions = {
	default: async ({ request }) => {
		const formData = await request.formData();
		const content = formData.get('content');

		if (typeof content !== 'string' || content.trim() === '') {
			return fail(400, {
				content,
				message: 'You have to type something to stash it.'
			});
		}

		const { data: stash, error } = await addTextStashApiV1StashesTextPost({
			body: content
		});

		if (error || !stash) {
			console.error('Failed to create text stash:', error);

			return fail(500, {
				content,
				message: 'Could not create the stash. Please try again.'
			});
		}

		throw redirect(303, resolve('/[slug]', { slug: stash.slug }));
	}
};