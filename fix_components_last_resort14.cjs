const fs = require('fs');

function fixFile(filePath, search, replace) {
  if (!fs.existsSync(filePath)) {
    console.log(`File not found: ${filePath}`);
    return;
  }
  let content = fs.readFileSync(filePath, 'utf-8');
  content = content.replace(search, replace);
  fs.writeFileSync(filePath, content);
}


fixFile('package.json', '    "build": "tsc && node --experimental-strip-types --no-warnings=ExperimentalWarning scripts/post-build.ts",', '    "build": "node --experimental-strip-types --no-warnings=ExperimentalWarning scripts/post-build.ts",');
fixFile('package.json', '    "gen": "npm run build && npm run docs:generate && npm run cli:generate && npm run update-tool-call-metrics && npm run format",', '    "gen": "npm run docs:generate && npm run cli:generate && npm run update-tool-call-metrics && npm run format",');
