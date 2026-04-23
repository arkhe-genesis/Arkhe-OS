/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import js from '@eslint/js';
import stylisticPlugin from '@stylistic/eslint-plugin';
import {defineConfig, globalIgnores} from 'eslint/config';
import importPlugin from 'eslint-plugin-import';
import globals from 'globals';
import tseslint from 'typescript-eslint';

import localPlugin from './scripts/eslint_rules/local-plugin.js';

export default defineConfig([
  globalIgnores([
    '**/node_modules',
    '**/build/',
    'tests/tools/fixtures/',
    'src/third_party/lighthouse-devtools-mcp-bundle.js',
  ]),
  importPlugin.flatConfigs.typescript,
  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',

      globals: {
        ...globals.node,
      },

      parserOptions: {
        projectService: {
          allowDefaultProject: [
            '.prettierrc.cjs',
            'puppeteer.config.cjs',
            'eslint.config.mjs',
            'rollup.config.mjs',
            'skills/memory-leak-debugging/references/compare_snapshots.js',
            'src/index.ts',
            'src/main.tsx',
            'src/issue-descriptions.ts',
            'skills/career-ops/dedup-tracker.mjs',
            'skills/career-ops/generate-pdf.mjs',
            'skills/career-ops/merge-tracker.mjs',
            'skills/career-ops/normalize-statuses.mjs',
            'skills/career-ops/verify-pipeline.mjs',
            'snap/src/index.ts',
            'src/gpd_bridge/index.js',
            'src/mirofish_bridge/index.js',
            'src/storage/embryovault.js',
            'src/velxio_bridge/index.js',
            'src/workers/inference.worker.js',
            'test_btc.ts',
            'test_lucent.ts',
            'trigger_handshake.js',
            'verify_design_final.test.ts',
            'vite.config.ts',
          ],
        },
      },

      parser: tseslint.parser,
    },

    plugins: {
      js,
      '@local': localPlugin,
      '@typescript-eslint': tseslint.plugin,
      '@stylistic': stylisticPlugin,
    },

    settings: {
      'import/resolver': {
        typescript: true,
      },
    },

    extends: ['js/recommended'],
  },
  tseslint.configs.recommended,
  tseslint.configs.stylistic,
  {
    name: 'TypeScript rules',
    rules: {
      '@local/check-license': 'error',
      curly: ['error', 'all'],

      'no-undef': 'off',
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
        },
      ],
      '@typescript-eslint/no-explicit-any': [
        'error',
        {
          ignoreRestArgs: true,
        },
      ],
      // This optimizes the dependency tracking for type-only files.
      '@typescript-eslint/consistent-type-imports': 'error',
      // So type-only exports get elided.
      '@typescript-eslint/consistent-type-exports': 'error',
      // Prefer interfaces over types for shape like.
      '@typescript-eslint/consistent-type-definitions': ['error', 'interface'],
      '@typescript-eslint/array-type': [
        'error',
        {
          default: 'array-simple',
        },
      ],
      '@typescript-eslint/no-floating-promises': 'error',

      'import/order': [
        'error',
        {
          'newlines-between': 'always',

          alphabetize: {
            order: 'asc',
            caseInsensitive: true,
          },
        },
      ],

      'import/no-cycle': [
        'error',
        {
          maxDepth: Infinity,
        },
      ],

      'import/enforce-node-protocol-usage': ['error', 'always'],

      '@stylistic/function-call-spacing': 'error',
      '@stylistic/semi': 'error',

      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              regex: '.*chrome-devtools-frontend/(?!mcp/mcp.js$).*',
              message:
                'Import only the devtools-frontend code exported via node_modules/chrome-devtools-frontend/mcp/mcp.js',
            },
          ],
        },
      ],
    },
  },
  {
    name: 'Source files',
    files: ['src/**/*.ts'],
    rules: {
      '@local/no-direct-third-party-imports': 'error',
    },
  },
  {
    name: 'Tools definitions',
    files: ['src/tools/**/*.ts'],
    rules: {
      '@local/enforce-zod-schema': 'error',
    },
  },
  {
    name: 'Tests',
    files: ['**/*.test.ts'],
    rules: {
      // With the Node.js test runner, `describe` and `it` are technically
      // promises, but we don't need to await them.
      '@typescript-eslint/no-floating-promises': 'off',
    },
  },
]);
