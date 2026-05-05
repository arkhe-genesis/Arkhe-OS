const fs = require('fs');
let content = fs.readFileSync('eslint.config.mjs', 'utf8');
content = content.replace("extends: ['js/recommended'],", "");
fs.writeFileSync('eslint.config.mjs', content);
