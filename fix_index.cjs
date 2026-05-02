const fs = require('fs');

let file = 'src/index.ts';
let c = fs.readFileSync(file, 'utf8');

c = c.replace(/import \{write_primordial_seed\} from "\.\/tools\/write_primordial_seed";/, 'import {write_primordial_seed} from "./tools/write_primordial_seed";\nimport {tribev2_predict} from "./tools/tribev2";');
c = c.replace(/write_primordial_seed\n\s*\}\s*;/g, 'write_primordial_seed,\n  tribev2_predict\n};');

fs.writeFileSync(file, c, 'utf8');
