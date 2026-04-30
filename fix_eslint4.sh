sed -i "s/import {defineConfig, globalIgnores} from 'eslint\/config';/import {config as defineConfig} from 'typescript-eslint';\nimport pkg from 'eslint';\nconst {globalIgnores} = pkg;/" eslint.config.mjs
sed -i 's/projectService: {/projectService: {\n          maximumDefaultProjectFileMatchCount_THIS_WILL_SLOW_DOWN_LINTING: 100,/g' eslint.config.mjs
