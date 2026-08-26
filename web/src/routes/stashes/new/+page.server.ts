import { fail, redirect } from '@sveltejs/kit';
import type { Actions } from './$types';
import { addBinaryStashApiV1StashesFilePost, addTextStashApiV1StashesTextPost } from '$lib/client';
import { resolve } from '$app/paths';

export const actions: Actions = {
	default: async ({ request }) => {
		const formData = await request.formData();
		const text = formData.get('text');
		const file = formData.get('file');

		const hasText = typeof text === 'string' && text.trim() !== '';
		const hasFile = file instanceof File && file.size > 0;

		console.log(`text: ${text}`);
		console.log(`hasFile: ${hasFile}`);

		if (!hasText && !hasFile) {
			return fail(422, {message: "You haven't submitted anything for stashing!"});
		}

		if (hasText && hasFile) {
			return fail(422, {message: "Choose to stash either some text or a file, but not both."})
		}

		if (hasText) {
			const { data: stash, error } = await addTextStashApiV1StashesTextPost({
				body: text
			});

			if (error || !stash) {
				console.error('Failed to create text stash:', error);

				return fail(500, {message: 'Could not create the stash. Please try again.'});
			}
			throw redirect(303, resolve('/[slug]', { slug: stash.slug }));
		}

		if (hasFile) {
			console.log("Got a file");
			const { data: stash, error } = await addBinaryStashApiV1StashesFilePost({
				body: {file}
			})

			if (error || !stash) {
				console.error('Failed to create file stash:', error);

				return fail(500, {message: 'Could not create the stash. Please try again.'});
			}
			throw redirect(303, resolve('/[slug]', { slug: stash.slug }));
		}

		
	}
} satisfies Actions;