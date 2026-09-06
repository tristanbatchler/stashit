import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

const config = {
	preprocess: vitePreprocess(),
	kit: {
		adapter: adapter(),
		env: {
			dir: '..'
		},
		typescript: {
			// This safely forces SvelteKit's generated tsconfig.json to accept the extensions
			config: (config) => {
				config.compilerOptions = {
					...config.compilerOptions,
					allowImportingTsExtensions: true,
					noEmit: true
				};
				return config;
			}
		}
	},
	compilerOptions: {
		// Force runes mode except for libraries (remove in Svelte 6 if unwanted)
		runes: ({ filename }) =>
			filename.split(/[/\\]/).includes('node_modules') ? undefined : true
	}
};

export default config;
