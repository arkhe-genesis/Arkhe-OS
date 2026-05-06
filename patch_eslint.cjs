const fs = require('fs');
let content = fs.readFileSync('eslint.config.mjs', 'utf8');
content = content.replace("'**/build/',", "'**/build/',\n    'evm-smith/',");
fs.writeFileSync('eslint.config.mjs', content);
