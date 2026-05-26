import twilio from 'twilio';
import { config } from '../config.js';

export function verifyTwilioSignature(request, reply, done) {
  const signature = request.headers['x-twilio-signature'];
  if (!signature) {
    return reply.code(401).send({ error: 'Missing X-Twilio-Signature' });
  }

  const proto = request.headers['x-forwarded-proto'] ?? request.protocol;
  const host = request.headers['x-forwarded-host'] ?? request.headers.host;
  const url = `${proto}://${host}${request.url}`;

  const params = request.body && typeof request.body === 'object' ? request.body : {};

  const valid = twilio.validateRequest(
    config.TWILIO_AUTH_TOKEN,
    signature,
    url,
    params,
  );

  if (!valid) {
    request.log.warn({ url }, 'Twilio signature validation failed');
    return reply.code(403).send({ error: 'Invalid Twilio signature' });
  }
  done();
}
