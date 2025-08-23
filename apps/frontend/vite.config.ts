/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // @ts-ignore
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    include: ['src/**/*.{test,spec}.{js,ts,jsx,tsx}'],
    exclude: [
      'node_modules',
      'dist',
      'tests/**',
      '**/tests/**',
      '**/*.e2e.{test,spec}.{js,ts,jsx,tsx}'
    ],
    transformMode: {
      web: [/echarts-for-react/],
    },
  },
});
