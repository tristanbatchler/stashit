import { browser } from '$app/environment';
import type { CreateClientConfig } from '$lib/client/client.gen';

export const createClientConfig: CreateClientConfig = (config) => {
    const envBaseUrl = process.env.API_BASE_URL;
    console.log(`envBaseUrl = ${envBaseUrl}`);
    return {
        ...config,
        baseUrl: browser ? '/' : envBaseUrl
    };
}