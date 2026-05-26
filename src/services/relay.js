import { config } from '../config.js';

export async function fanOutWebhook(kind, payload) {
  if (!config.RELAY_DOWNSTREAM_URLS.length) return;
  await Promise.allSettled(
    config.RELAY_DOWNSTREAM_URLS.map((url) =>
      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ kind, payload, at: new Date().toISOString() }),
      }),
    ),
  );
}
