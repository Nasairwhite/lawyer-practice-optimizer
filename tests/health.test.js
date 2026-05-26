import { test } from 'node:test';
import assert from 'node:assert/strict';

process.env.TWILIO_ACCOUNT_SID = 'ACtestaccount';
process.env.TWILIO_AUTH_TOKEN = 'testtoken';

test('config parses minimal env', async () => {
  const { config } = await import('../src/config.js');
  assert.equal(config.TWILIO_ACCOUNT_SID, 'ACtestaccount');
  assert.equal(config.CLAUDE_AUTOREPLY, false);
});
