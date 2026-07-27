import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig(({ mode }) => ({
  plugins: [svelte()],
  base: mode === 'production' ? '/Arteteca/' : '/',
  build: {
    target: 'es2022',
    cssCodeSplit: true,
    sourcemap: true,
  },
}));
