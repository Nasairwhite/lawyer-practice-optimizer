import twilio from 'twilio';
import { config } from '../config.js';
import { sendSms } from '../services/twilio.js';
import { generateSmsReply } from '../services/claude.js';
import { verifyTwilioSignature } from '../middleware/twilioSignature.js';
import { fanOutWebhook } from '../services/relay.js';

const { MessagingResponse } = twilio.twiml;

export default async function smsRoutes(fastify) {
  fastify.post(
    '/webhooks/sms',
    { preHandler: verifyTwilioSignature },
    async (request, reply) => {
      const { From, Body, MessageSid } = request.body ?? {};
      request.log.info({ MessageSid, From }, 'inbound sms');

      fanOutWebhook('sms', request.body).catch((err) =>
        request.log.error({ err }, 'relay fan-out failed'),
      );

      const twiml = new MessagingResponse();

      if (config.CLAUDE_AUTOREPLY && config.ANTHROPIC_API_KEY) {
        try {
          const replyText = await generateSmsReply({
            inboundBody: Body ?? '',
            from: From ?? 'unknown',
          });
          twiml.message(replyText);
        } catch (err) {
          request.log.error({ err }, 'claude reply failed');
          twiml.message('Sorry, the assistant is temporarily unavailable.');
        }
      }

      reply.header('Content-Type', 'text/xml').send(twiml.toString());
    },
  );

  fastify.post('/sms/send', async (request, reply) => {
    const { to, body, from } = request.body ?? {};
    if (!to || !body) {
      return reply.code(400).send({ error: 'to and body are required' });
    }
    const message = await sendSms({ to, from, body });
    return { sid: message.sid, status: message.status };
  });
}
