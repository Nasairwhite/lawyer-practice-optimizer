import Fastify from 'fastify';
import formbody from '@fastify/formbody';
import sensible from '@fastify/sensible';
import { config } from './config.js';
import smsRoutes from './routes/sms.js';
import proxyRoutes from './routes/proxy.js';

const app = Fastify({
  logger: {
    level: config.LOG_LEVEL,
    transport:
      process.env.NODE_ENV !== 'production'
        ? { target: 'pino-pretty', options: { colorize: true } }
        : undefined,
  },
  trustProxy: true,
});

await app.register(formbody);
await app.register(sensible);

app.get('/health', async () => ({ ok: true, ts: Date.now() }));

await app.register(smsRoutes);
await app.register(proxyRoutes);

app.setErrorHandler((err, request, reply) => {
  request.log.error({ err }, 'unhandled error');
  reply.code(err.statusCode ?? 500).send({ error: err.message });
});

try {
  await app.listen({ port: config.PORT, host: config.HOST });
} catch (err) {
  app.log.error(err);
  process.exit(1);
}
