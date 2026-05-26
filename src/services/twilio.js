import twilio from 'twilio';
import { config } from '../config.js';

export const twilioClient = twilio(
  config.TWILIO_ACCOUNT_SID,
  config.TWILIO_AUTH_TOKEN,
);

export async function sendSms({ to, from, body }) {
  return twilioClient.messages.create({
    to,
    from: from ?? config.TWILIO_FROM_NUMBER,
    body,
  });
}

let cachedProxyServiceSid = config.TWILIO_PROXY_SERVICE_SID || null;

export async function getOrCreateProxyService(uniqueName = 'twilio-proxy-default') {
  if (cachedProxyServiceSid) return cachedProxyServiceSid;
  const service = await twilioClient.proxy.v1.services.create({
    uniqueName,
    callbackUrl: config.PUBLIC_BASE_URL
      ? `${config.PUBLIC_BASE_URL}/webhooks/proxy`
      : undefined,
  });
  cachedProxyServiceSid = service.sid;
  return service.sid;
}

export async function createMaskedSession({ participants, ttlSeconds = 86400 }) {
  const serviceSid = await getOrCreateProxyService();
  const session = await twilioClient.proxy.v1
    .services(serviceSid)
    .sessions.create({ ttl: ttlSeconds, mode: 'message-and-voice' });

  for (const p of participants) {
    await twilioClient.proxy.v1
      .services(serviceSid)
      .sessions(session.sid)
      .participants.create({
        identifier: p.phoneNumber,
        friendlyName: p.friendlyName,
      });
  }
  return { sessionSid: session.sid, serviceSid };
}

export async function closeMaskedSession({ sessionSid }) {
  const serviceSid = await getOrCreateProxyService();
  return twilioClient.proxy.v1
    .services(serviceSid)
    .sessions(sessionSid)
    .update({ status: 'closed' });
}
