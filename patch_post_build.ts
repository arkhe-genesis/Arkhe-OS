import * as fs from 'node:fs';

const file = 'scripts/post-build.ts';
let content = fs.readFileSync(file, 'utf8');

const exportStr = `
  const thirdPartySrcDir = path.join(BUILD_DIR, 'src', 'third_party');
  fs.mkdirSync(thirdPartySrcDir, {recursive: true});

  // Re-export the bundle logic from original index.ts
  const originalThirdPartySrc = path.join(process.cwd(), 'src', 'third_party', 'index.ts');
  const originalThirdPartyContent = fs.readFileSync(originalThirdPartySrc, 'utf8');
  let compiledContent = originalThirdPartyContent.replace(/import 'core-js\\/[^']+'\\n/g, '');
  // Let rollup resolve the real path instead of relative to the generated index.ts
  compiledContent = compiledContent.replace(/export \\* as DevTools from '\\.\\.\\/\\.\\.\\/node_modules\\/chrome-devtools-frontend\\/mcp\\/mcp\\.ts';/, "export * as DevTools from '../../../node_modules/chrome-devtools-frontend/mcp/mcp.js';");
  writeFile(path.join(thirdPartySrcDir, 'index.ts'), compiledContent);

  const devtoolsFormatterWorkerFile = path.join(thirdPartySrcDir, 'devtools-formatter-worker.js');
  writeFile(devtoolsFormatterWorkerFile, "export {};\\n");
`;

if (!content.includes('thirdPartySrcDir')) {
    content = content.replace('main();', exportStr + '\nmain();\n');
} else {
    // Already patched, replace the chunk
    content = content.replace(/const thirdPartySrcDir = [\s\S]+?\}\s*/, exportStr);
}

fs.writeFileSync(file, content);
