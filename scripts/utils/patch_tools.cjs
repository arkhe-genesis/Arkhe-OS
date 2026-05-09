const fs = require('fs');
let content = fs.readFileSync('src/tools/tools.ts', 'utf8');

const lines = content.split('\n');
const fixedLines = lines.filter((line, index) => {
    if (line.includes("import * as gnoTools from './gno.js';")) {
        return lines.indexOf(line) === index;
    }
    return true;
});

fs.writeFileSync('src/tools/tools.ts', fixedLines.join('\n'));
