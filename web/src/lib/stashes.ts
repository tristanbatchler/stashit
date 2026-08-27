import {
	addBinaryStashApiV1StashesFilePost,
	addTextStashApiV1StashesTextPost,
} from '$lib/client';

import { createUploadClient } from '$lib/upload-client';

export type CreatedStash = {
	slug: string;
};

function getErrorMessage(error: unknown, fallback: string): string {
	if (
		typeof error === 'object' &&
		error !== null &&
		'detail' in error
	) {
		return String(error.detail);
	}

	return fallback;
}

export async function createStash(
	file: File | undefined,
	text: string,
	onProgress: (loaded: number, total: number) => void,
): Promise<CreatedStash> {
	if (file && file.size > 0) {
		const client = createUploadClient(onProgress);

		const response = await addBinaryStashApiV1StashesFilePost({
			client,
			body: { file },
		});

		if (response.error) {
			throw new Error(
				getErrorMessage(response.error, 'Upload failed'),
			);
		}

		return response.data;
	}

	if (text.trim() !== '') {
		const response = await addTextStashApiV1StashesTextPost({
			body: text,
		});

		if (response.error) {
			throw new Error(
				getErrorMessage(response.error, 'Request failed'),
			);
		}

		return response.data;
	}

	throw new Error(
		"You haven't submitted anything for stashing!",
	);
}