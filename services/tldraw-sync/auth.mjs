import crypto from 'node:crypto';

const SECRET = (
  process.env.WHITEBOARD_SYNC_SECRET
  || process.env.SECRET_KEY
  || process.env.DJANGO_SECRET_KEY
  || ''
).trim();

function b64urlDecode(value) {
  const pad = '='.repeat((4 - (value.length % 4)) % 4);
  return Buffer.from(value + pad, 'base64url');
}

export function verifyWhiteboardToken(token, roomId) {
  if (!SECRET || !token || typeof token !== 'string') {
    return false;
  }

  const dot = token.lastIndexOf('.');
  if (dot <= 0) {
    return false;
  }

  const body = token.slice(0, dot);
  const sig = token.slice(dot + 1);
  if (!body || !sig) {
    return false;
  }

  const expected = crypto.createHmac('sha256', SECRET).update(body).digest('hex');
  const sigBuf = Buffer.from(sig);
  const expectedBuf = Buffer.from(expected);
  if (sigBuf.length !== expectedBuf.length) {
    return false;
  }
  if (!crypto.timingSafeEqual(sigBuf, expectedBuf)) {
    return false;
  }

  let payload;
  try {
    payload = JSON.parse(b64urlDecode(body).toString('utf8'));
  } catch {
    return false;
  }

  if (payload.conf !== String(roomId)) {
    return false;
  }

  if (!payload.sub || typeof payload.exp !== 'number') {
    return false;
  }

  if (payload.exp < Math.floor(Date.now() / 1000)) {
    return false;
  }

  return true;
}
