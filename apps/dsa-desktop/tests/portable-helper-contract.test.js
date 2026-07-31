const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');

const helperPath = path.join(
  __dirname,
  '..',
  'portable-update',
  'portable-update-helper.ps1',
);


test('portable helper avoids the PowerShell HOME automatic variable', () => {
  const script = fs.readFileSync(helperPath, 'utf8');

  assert.doesNotMatch(script, /^\s*\$home\s*=/im);
  assert.match(script, /\$homeResponse\s*=\s*Invoke-WebRequest/);
  assert.match(script, /\$homeResponse\.StatusCode/);
});
