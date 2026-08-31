// web/src/routes/ip/[ip_addr]/+page.server.ts
import {
	addIpBanApiV1IpIpAddrBanPost,
	getActiveIpBanApiV1IpIpAddrBansActiveGet,
	listIpActivityApiV1IpIpAddrActivityGet,
	revokeBanApiV1IpBansBanIdDelete
} from '$lib/client';
import { error, fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({
	params,
	url,
	parent,
	request
}) => {
	const { user } = await parent();

	if (!user?.is_admin) {
		error(403, 'You are not allowed to do that');
	}

	const ipAddress = params.ip_addr;
	const page = Number(url.searchParams.get('page') ?? '1');
	const take = Number(url.searchParams.get('take') ?? '25');

	if (
		!Number.isInteger(page) ||
		page < 1 ||
		!Number.isInteger(take) ||
		take < 1
	) {
		error(400, 'Invalid pagination parameters');
	}

	const cookie = request.headers.get('cookie') ?? '';

	const [activityResult, activeBanResult] = await Promise.all([
		listIpActivityApiV1IpIpAddrActivityGet({
			path: { ip_addr: ipAddress },
			query: { page, take },
			credentials: 'include',
			headers: { cookie }
		}),
		getActiveIpBanApiV1IpIpAddrBansActiveGet({
			path: { ip_addr: ipAddress },
			credentials: 'include',
			headers: { cookie }
		})
	]);

	if (activityResult.error || !activityResult.data) {
		error(activityResult.response?.status ?? 500, {
			message:
				activityResult.error && 'detail' in activityResult.error
					? String(activityResult.error.detail)
					: 'Could not load IP activity'
		});
	}

	if (activeBanResult.error) {
		error(activeBanResult.response?.status ?? 500, {
			message:
				activeBanResult.error && 'detail' in activeBanResult.error
					? String(activeBanResult.error.detail)
					: 'Could not load active ban'
		});
	}

	return {
		ipAddress,
		activity: activityResult.data,
		activeBan: activeBanResult.data ?? null,
		page,
		take
	};
};

export const actions: Actions = {
	ban: async ({ params, request }) => {
		const formData = await request.formData();

		const reasonValue = formData.get('reason');
		const expiresValue = formData.get('expires');

		const reason =
			typeof reasonValue === 'string' && reasonValue.trim().length > 0
				? reasonValue.trim()
				: null;

		let expires: string | null = null;

		if (typeof expiresValue === 'string' && expiresValue.length > 0) {
			const date = new Date(expiresValue);

			if (Number.isNaN(date.getTime())) {
				return fail(400, {
					banError: 'Invalid expiry date'
				});
			}

			expires = date.toISOString();
		}

		const cookie = request.headers.get('cookie') ?? '';

		const { data, error: banError, response } =
			await addIpBanApiV1IpIpAddrBanPost({
				path: {
					ip_addr: params.ip_addr
				},
				body: {
					expires,
					reason
				},
				credentials: 'include',
				headers: {
					cookie
				}
			});

		if (banError || !data) {
			return fail(response?.status ?? 500, {
				banError:
					banError && 'detail' in banError
						? String(banError.detail)
						: 'Could not ban IP address'
			});
		}

		return {
			banSuccess: true
		};
	},

	revoke: async ({ request }) => {
		const formData = await request.formData();
		const banIdValue = formData.get('ban_id');

		if (typeof banIdValue !== 'string') {
			return fail(400, {
				revokeError: 'Ban ID is required'
			});
		}

		const banId = Number(banIdValue);

		if (!Number.isInteger(banId) || banId <= 0) {
			return fail(400, {
				revokeError: 'Invalid ban ID'
			});
		}

		const reasonValue = formData.get('reason');
		const reason =
			typeof reasonValue === 'string' && reasonValue.trim().length > 0
				? reasonValue.trim()
				: null;

		const cookie = request.headers.get('cookie') ?? '';

		const { error: revokeError, response } =
			await revokeBanApiV1IpBansBanIdDelete({
				path: {
					ban_id: banId
				},
				body: reason,
				credentials: 'include',
				headers: {
					cookie
				}
			});

		if (revokeError) {
			return fail(response?.status ?? 500, {
				revokeError:
					revokeError && 'detail' in revokeError
						? String(revokeError.detail)
						: 'Could not revoke ban'
			});
		}

		return {
			revokeSuccess: true
		};
	}
};