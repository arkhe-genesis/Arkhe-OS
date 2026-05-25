const { Arkhe, CONSTANTS } = require('./arkhe.js');
const assert = require('assert');

// Simple test file for arkhe.js logic

try {
  const arkhe = new Arkhe();
  const status = arkhe.status();

  assert.equal(status.version, "1.0.0");
  assert.equal(status.constants.PHI.toFixed(3), "1.618");

  console.log("arkhe.js tests passed.");
} catch (e) {
  console.error("Test failed", e);
  process.exit(1);
}
