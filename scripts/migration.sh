#!/bin/bash

# Migration script for Arkhe-OS refactoring

# Create additional directories
mkdir -p core/arkhe core/build core/types core/lib
mkdir -p runtime/typescript
mkdir -p config/docker config/kubernetes config/yaml config/dependencies config/platform config/secrets
mkdir -p scripts/deploy scripts/simulation scripts/utils scripts/validation scripts/testing
mkdir -p data/experimental data/results data/datasets data/astronomy data/models
mkdir -p tools/.ai-integrations/vscode tools/.ai-integrations/cursor tools/.ai-integrations/other
mkdir -p packages
mkdir -p archive/patches archive/one-off-fixes archive/old-docs archive/old-diagnostics archive/abandoned-packages archive/old-scripts archive/old-ai-integrations

# Move Docker configs
mv Dockerfile* docker-compose*.yml .dockerignore config/docker/ 2>/dev/null || true

# Move build files
mv CMakeLists.txt Makefile core/build/ 2>/dev/null || true

# Move config files
mv config.yaml config/core.yaml 2>/dev/null || true
mv config/*.yaml config/yaml/ 2>/dev/null || true
mv requirements*.txt config/dependencies/ 2>/dev/null || true

# Move experimental data
mv dosagem_*.csv inoculation_*.csv plate_layout.csv data/experimental/ 2>/dev/null || true

# Move results
mv *_results.json cuda_stress_test_results.json benchmark_results.json data/results/ 2>/dev/null || true

# Move datasets
mv *.npz *.pkl data/datasets/ 2>/dev/null || true

# Move diagnostic images
mkdir -p docs/figures/diagnostics
mv *.png docs/figures/diagnostics/ 2>/dev/null || true

# Move arkhe-* packages (keep active ones)
mv arkhe-chain-node packages/chain-node 2>/dev/null || true
mv arkhe-core packages/core 2>/dev/null || true
mv arkhe-qpu packages/qpu 2>/dev/null || true
# Add more as needed

# Archive unused packages
mv arkhe_clinical arkhe_1q arkhe_10q archive/abandoned-packages/ 2>/dev/null || true

# Move AI integrations
mv .continue tools/.ai-integrations/vscode/ 2>/dev/null || true
mv .claude tools/.ai-integrations/vscode/ 2>/dev/null || true
mv .windsurf tools/.ai-integrations/windsurf 2>/dev/null || true
# Archive old
mv .bob .codebuddy .crush archive/old-ai-integrations/ 2>/dev/null || true

# Archive patches
mv fix_*.patch archive/patches/ 2>/dev/null || true
mv fix_components*.cjs archive/one-off-fixes/ 2>/dev/null || true

# Archive old versions
mv README_v*.md archive/old-docs/ 2>/dev/null || true
mv IMPLEMENTATION_SUMMARY_v3_0*.md archive/old-docs/ 2>/dev/null || true
mv setup.py.bak archive/old-scripts/ 2>/dev/null || true

# Move other files
mv *.csv data/experimental/ 2>/dev/null || true
mv *.json data/results/ 2>/dev/null || true
mv *.fits data/astronomy/ 2>/dev/null || true
mv *.pdf docs/ 2>/dev/null || true
mv *.xlsx docs/ 2>/dev/null || true
mv *.gcode docs/ 2>/dev/null || true
mv *.circom contracts/ 2>/dev/null || true
mv *.js *.cjs *.mjs scripts/utils/ 2>/dev/null || true
mv *.ts config/ 2>/dev/null || true
mv *.md docs/ 2>/dev/null || true
mv *.txt docs/ 2>/dev/null || true
mv pyproject.toml core/ 2>/dev/null || true
mv package.json . 2>/dev/null || true
mv package-lock.json . 2>/dev/null || true
mv tsconfig*.json core/ 2>/dev/null || true
mv pytest.ini tests/ 2>/dev/null || true
mv netlify.toml config/ 2>/dev/null || true
mv vercel.json config/ 2>/dev/null || true
mv VERSION CHANGELOG.md CITATION.cff .release-please-manifest.json config/release/ 2>/dev/null || true
mv setup.py setup.sh scripts/ 2>/dev/null || true

echo "Migration completed. Check for any remaining files."