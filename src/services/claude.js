import Anthropic from '@anthropic-ai/sdk';
import { config } from '../config.js';

let client = null;

function getClient() {
  if (!config.ANTHROPIC_API_KEY) return null;
  if (!client) client = new Anthropic({ apiKey: config.ANTHROPIC_API_KEY });
  return client;
}

export async function generateSmsReply({ inboundBody, from, history = [] }) {
  const anthropic = getClient();
  if (!anthropic) {
    throw new Error('ANTHROPIC_API_KEY is not configured');
  }

  const messages = [
    ...history,
    { role: 'user', content: `From ${from}: ${inboundBody}` },
  ];

  const resp = await anthropic.messages.create({
    model: config.ANTHROPIC_MODEL,
    max_tokens: config.ANTHROPIC_MAX_TOKENS,
    system: config.CLAUDE_SYSTEM_PROMPT,
    messages,
  });

  const text = resp.content
    .filter((b) => b.type === 'text')
    .map((b) => b.text)
    .join('\n')
    .trim();

  return text.slice(0, 1500);
}
