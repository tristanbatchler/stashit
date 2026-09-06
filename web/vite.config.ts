import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
	const env = loadEnv(mode, '..', '');
	console.log(`Identified API_BASE_URL to be ${env.API_BASE_URL}`);

	return {
		server: {
			proxy: {
				'/api': {
					target: env.API_BASE_URL
				}
			}
		},
		plugins: [sveltekit()],
		css: {
			preprocessorOptions: {
				scss: {
					quietDeps: true
				}
			}
		}
	};
});