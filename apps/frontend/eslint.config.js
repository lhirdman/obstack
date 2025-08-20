// For more info, see https://github.com/storybookjs/eslint-plugin-storybook#configuration-flat-config-format
import storybook from "eslint-plugin-storybook";

import tsParser from '@typescript-eslint/parser'

export default [{
  ignores: ['dist', 'node_modules', '*.config.js', '*.config.ts']
}, {
  files: ['**/*.{ts,tsx}'],
  languageOptions: {
    parser: tsParser,
    ecmaVersion: 2020,
    sourceType: 'module',
    parserOptions: {
      ecmaFeatures: {
        jsx: true
      },
      project: './tsconfig.eslint.json'
    }
  },
  rules: {
    'no-unused-vars': 'off',
    'no-undef': 'off', // TypeScript handles this
    'prefer-const': 'error',
    'no-var': 'error'
  }
}, ...storybook.configs["flat/recommended"]];