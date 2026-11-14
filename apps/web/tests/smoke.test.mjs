import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';

test('Next.js home page exists', () => {
  assert.ok(existsSync('src/app/page.tsx'));
});
