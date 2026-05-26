import {
  createMaskedSession,
  closeMaskedSession,
  getOrCreateProxyService,
} from '../services/twilio.js';
import { verifyTwilioSignature } from '../middleware/twilioSignature.js';
import { fanOutWebhook } from '../services/relay.js';

export default async function proxyRoutes(fastify) {
  fastify.post('/proxy/sessions', async (request, reply) => {
    const { participants, ttlSeconds } = request.body ?? {};
    if (!Array.isArray(participants) || participants.length < 2) {
      return reply
        .code(400)
        .send({ error: 'participants must be an array of at least 2 entries' });
    }
    const result = await createMaskedSession({ participants, ttlSeconds });
    return result;
  });

  fastify.delete('/proxy/sessions/:sessionSid', async (request, reply) => {
    const { sessionSid } = request.params;
    await closeMaskedSession({ sessionSid });
    return { closed: true, sessionSid };
  });

  fastify.get('/proxy/service', async () => {
    const sid = await getOrCreateProxyService();
    return { serviceSid: sid };
  });

  fastify.post(
    '/webhooks/proxy',
    { preHandler: verifyTwilioSignature },
    async (request, reply) => {
      request.log.info({ body: request.body }, 'proxy webhook');
      fanOutWebhook('proxy', request.body).catch((err) =>
        request.log.error({ err }, 'relay fan-out failed'),
      );
      return reply.send({ ok: true });
    },
  );
}
