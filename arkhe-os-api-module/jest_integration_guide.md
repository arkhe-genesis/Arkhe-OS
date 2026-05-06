# Jest Testing Framework Integration (Substrato 254)

This module implements the Jest testing framework for the `arkhe-os-api-module` as required by Substrate 254.

## Setup

1. The environment is configured with `jest`, `ts-jest`, `ts-node` and `@types/jest`.
2. The config file `jest.config.ts` handles the mapping of the `src` and `tests` directories.
3. The TypeScript compiler uses `tsconfig.json`.

To run tests with coverage reporting (as required by the guidelines to maintain 80% coverage):
```bash
npm install
npm run test -- --coverage
```

## Structure

- `src/index.ts`: The main application code exporting types and projection algorithms.
- `tests/`: Directory containing specific tests (currently `coherence.test.ts`).

## Rules
- Snapshots should be used for validation of LFIR graph nodes.
- Coherence computations must map to `[0, 1]`.
