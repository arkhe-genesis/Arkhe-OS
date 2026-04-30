sed -i "s/import pkg from 'eslint';\nconst {globalIgnores} = pkg;/\n/g" eslint.config.mjs
sed -i "s/globalIgnores(/{\n    ignores: /g" eslint.config.mjs
sed -i 's/  ]),/  ], },/g' eslint.config.mjs
