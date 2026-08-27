export function xhrFetch(
	onProgress: (loaded: number, total: number) => void
): typeof fetch {
	return async (input, init) => {
		const request =
			input instanceof Request
				? input
				: new Request(input, init);

		const contentType =
			request.headers.get('Content-Type') ?? '';

		let body: XMLHttpRequestBodyInit | null = null;

		if (contentType.startsWith('multipart/form-data')) {
			body = await request.formData();
		} else {
			body = await request.text();
		}

		return await new Promise<Response>((resolve, reject) => {
			const xhr = new XMLHttpRequest();

			xhr.open(request.method, request.url);

			request.headers.forEach((value, key) => {
				// Critical: browser/XHR must generate the multipart
				// boundary when sending FormData.
				if (
					key.toLowerCase() !== 'content-type' ||
					!(body instanceof FormData)
				) {
					xhr.setRequestHeader(key, value);
				}
			});

			xhr.upload.onprogress = (event) => {
				if (event.lengthComputable) {
					onProgress(event.loaded, event.total);
				}
			};

			xhr.onload = () => {
				const headers = new Headers();

				for (const line of xhr
					.getAllResponseHeaders()
					.split(/\r?\n/)
					.filter(Boolean)) {
					const index = line.indexOf(':');

					if (index !== -1) {
						headers.set(
							line.slice(0, index),
							line.slice(index + 1).trim()
						);
					}
				}

				resolve(
					new Response(xhr.responseText, {
						status: xhr.status,
						statusText: xhr.statusText,
						headers
					})
				);
			};

			xhr.onerror = () => {
				reject(new TypeError('Network request failed'));
			};

			xhr.onabort = () => {
				reject(
					new DOMException(
						'Request aborted',
						'AbortError'
					)
				);
			};

			if (request.signal) {
				request.signal.addEventListener(
					'abort',
					() => xhr.abort(),
					{ once: true }
				);
			}

			xhr.send(body);
		});
	};
}