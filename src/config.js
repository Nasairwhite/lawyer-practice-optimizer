import 'dotenv/config';
import { z } from 'zod';

const schema = z.object({
  PORT: z.coerce.number().default(3000),
  HOST: z.string().default('0.0.0.0'),
  LOG_LEVEL: z.string().default('info'),
  PUBLIC_BASE_URL: z.string().url().optional(),

  TWILIO_ACCOUNT_SID: z.string().startsWith('AC'),
  TWILIO_AUTH_TOKEN: z.string().min(1),
  TWILIO_FROM_NUMBER: z.string().optional(),
  TWILIO_PROXY_SERVICE_SID: z.string().optional(),

  ANTHROPIC_API_KEY: z.string().optional(),
  ANTHROPIC_MODEL: z.string().default('claude-opus-4-7'),
  ANTHROPIC_MAX_TOKENS: z.coerce.number().default(1024),

  CLAUDE_AUTOREPLY: z
    .string()
    .default('false')
    .transform((v) => v.toLowerCase() === 'true'),
  CLAUDE_SYSTEM_PROMPT: z
    .string()
    .default('You are a concise SMS assistant. Keep replies under 320 characters.'),

  RELAY_DOWNSTREAM_URLS: z
    .string()
    .default('')
    .transform((v) =>
      v
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
    ),
});

const parsed = schema.safeParse(process.env);
if (!parsed.success) {
  console.error('Invalid environment configuration:');
  console.error(parsed.error.flatten().fieldErrors);
  process.exit(1);
}

export const config = parsed.data;
