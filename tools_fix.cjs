const fs = require('fs');
let file = 'src/index.ts';
if (fs.existsSync(file)) {
    let content = fs.readFileSync(file, 'utf8');
    // Ensure tribev2_predict is exported correctly or registered
    console.log(content.includes('tribev2'));
}
