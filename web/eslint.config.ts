import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import svelte from 'eslint-plugin-svelte';
import globals from 'globals';
import { defineConfig } from 'eslint/config';

export default defineConfig(
	// 1. Global Ignores (Keep these safely isolated at the top)
	{
		ignores: [
			'**/.*/**',
			'**/.svelte-kit/**',
			'**/build/**',
			'**/dist/**',
			'**/node_modules/**',
			'**/src/lib/client/**'
		],
	},

	// 2. Extends
	{
		extends: [
			eslint.configs.recommended,
			...tseslint.configs.recommended,
			...svelte.configs['flat/recommended'],
		],
	},

	// 3. Globals & Base setup (DO NOT force tseslint.parser at this level)
	{
		files: ['**/*.{js,ts,svelte}'],
		languageOptions: {
			globals: {
				...globals.browser,
			},
		},
	},

	// 4. Pure TypeScript files setup
	{
		files: ['**/*.ts'],
		languageOptions: {
			parser: tseslint.parser, // Only use the TS parser for actual .ts files
		},
	},

	// 5. Svelte files setup
	{
		files: ['**/*.svelte'],
		languageOptions: {
			parserOptions: {
				// This lets eslint-plugin-svelte process the HTML/Svelte markup, 
				// and tells it to safely hand off the <script lang="ts"> bits to TypeScript
				parser: tseslint.parser,
			},
		},
	}
);
