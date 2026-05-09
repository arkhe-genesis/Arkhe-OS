const fs = require('fs');
const glob = require('glob');

const files = glob.sync('src/components/**/*.tsx');
files.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  let changed = false;

  if (content.includes('export default function Component() { return <div />; }')) {
    content = content.replace('export default function Component() { return <div />; }', 'export default function Component(props: any) { return <div />; }');
    changed = true;
  }

  if (changed) {
    fs.writeFileSync(file, content, 'utf8');
  }
});
