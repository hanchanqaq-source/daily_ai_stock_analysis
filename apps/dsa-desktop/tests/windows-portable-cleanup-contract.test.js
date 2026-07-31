'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const workflowPath = path.resolve(
  __dirname,
  '..',
  '..',
  '..',
  '.github',
  'workflows',
  'ci.yml',
);

const workflow = fs.readFileSync(workflowPath, 'utf8');

test('Windows portable ZIP verification retries final extraction cleanup', () => {
  assert.match(workflow, /function Remove-FinalExtractWithRetry/);
  assert.match(workflow, /for \(\$attempt = 1; \$attempt -le \$MaxAttempts; \$attempt\+\+\)/);
  assert.match(workflow, /Start-Sleep -Seconds 1/);

  const cleanupCalls = workflow.match(
    /Remove-FinalExtractWithRetry -Path \$finalExtract/g,
  ) || [];
  assert.equal(cleanupCalls.length, 2);

  assert.doesNotMatch(
    workflow,
    /^\s*Remove-Item -LiteralPath \$finalExtract -Recurse -Force\s*$/m,
  );
});
