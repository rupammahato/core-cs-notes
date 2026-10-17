import { createHash, randomBytes, randomUUID, timingSafeEqual } from 'node:crypto';
import { SignJWT, jwtVerify, generateKeyPair } from 'jose';
import { verifyPassword } from './password.mjs';

export class AuthError extends Error {
  constructor(status, code) { super(code); Object.assign(this, { status, code }); }
}
const deny = (code = 'unauthenticated') => { throw new AuthError(401, code); };
const opaque = () => randomBytes(32).toString('base64url');
const validOpaque = token => typeof token === 'string' && /^[A-Za-z0-9_-]{43}$/.test(token);
const digest = token => createHash('sha256').update(token).digest('hex');
const equal = (a, b) => typeof a === 'string' && typeof b === 'string' &&
  Buffer.byteLength(a) === Buffer.byteLength(b) && timingSafeEqual(Buffer.from(a), Buffer.from(b));

export async function createIdentity({
  passwordRecord, now = Date.now, keyPair,
  issuer = 'https://identity.example.test', audience = 'placement-api',
} = {}) {
  if (!passwordRecord) throw new TypeError('Supply a fixture credential record.');
  const keys = keyPair ?? await generateKeyPair('RS256');
  const user = { id: 'user-1', email: 'learner@example.test', name: 'Placement Learner' };
  const sessions = new Map();
  const families = new Map();
  const refreshRecords = new Map();

  async function login(email, password) {
    // The single fixture record doubles as the dummy record for unknown accounts.
    const correct = await verifyPassword(password, passwordRecord);
    if (email !== user.email || !correct) deny('invalid_credentials');
    return user.id;
  }
  function makeSession(subject, oldToken) {
    if (subject !== user.id) deny();
    if (validOpaque(oldToken)) sessions.delete(digest(oldToken));
    const token = opaque();
    const createdAt = now();
    const record = { subject, csrf: opaque(), createdAt, lastSeen: createdAt };
    sessions.set(digest(token), record);
    return { token, csrf: record.csrf };
  }
  function getSession(token) {
    if (!validOpaque(token)) deny();
    const key = digest(token);
    const record = sessions.get(key);
    const current = now();
    if (!record) deny();
    if (current - record.lastSeen >= 30_000 || current - record.createdAt >= 120_000) {
      sessions.delete(key);
      deny('session_expired');
    }
    record.lastSeen = current;
    return record;
  }
  function sessionView(token) {
    const record = getSession(token);
    return { user: { ...user }, csrfToken: record.csrf };
  }
  function logoutSession(token, csrf) {
    const record = getSession(token);
    if (!equal(csrf, record.csrf)) throw new AuthError(403, 'csrf_rejected');
    sessions.delete(digest(token));
  }
  async function issueAccess(subject) {
    if (subject !== user.id) deny();
    const seconds = Math.floor(now() / 1000);
    return new SignJWT({})
      .setProtectedHeader({ alg: 'RS256', typ: 'at+jwt', kid: 'demo-rsa-1' })
      .setIssuer(issuer).setAudience(audience).setSubject(subject)
      .setIssuedAt(seconds).setExpirationTime(seconds + 60).setJti(randomUUID())
      .sign(keys.privateKey);
  }
  async function accessView(token) {
    try {
      const { payload, protectedHeader } = await jwtVerify(token, keys.publicKey, {
        algorithms: ['RS256'], typ: 'at+jwt', issuer, audience,
        requiredClaims: ['sub', 'iat', 'exp', 'jti'],
        currentDate: new Date(now()), clockTolerance: 0,
      });
      const seconds = Math.floor(now() / 1000);
      if (payload.sub !== user.id || typeof payload.jti !== 'string' || !payload.jti ||
          !Number.isSafeInteger(payload.iat) || payload.iat > seconds ||
          !Number.isSafeInteger(payload.exp) || payload.exp <= payload.iat ||
          payload.exp - payload.iat > 60 || protectedHeader.kid !== 'demo-rsa-1') deny();
      return { user: { ...user } };
    } catch { deny('invalid_access_token'); }
  }
  function makeRefresh(subject) {
    if (subject !== user.id) deny();
    const familyId = randomUUID();
    const token = opaque();
    families.set(familyId, { subject, absoluteAt: now() + 300_000, revoked: false });
    refreshRecords.set(digest(token), { familyId, used: false });
    return token;
  }
  function rotateRefresh(token) {
    if (!validOpaque(token)) deny('invalid_refresh_token');
    const record = refreshRecords.get(digest(token));
    const family = record && families.get(record.familyId);
    if (!family || family.revoked || now() >= family.absoluteAt) deny('invalid_refresh_token');
    if (record.used) {
      family.revoked = true;
      deny('refresh_reuse');
    }
    // No await separates consumption from successor creation in this demo store.
    record.used = true;
    const next = opaque();
    refreshRecords.set(digest(next), { familyId: record.familyId, used: false });
    return { subject: family.subject, refreshToken: next };
  }
  function revokeRefresh(token) {
    if (!validOpaque(token)) return;
    const record = refreshRecords.get(digest(token));
    if (record) families.get(record.familyId).revoked = true;
  }
  return {
    login, makeSession, sessionView, logoutSession,
    issueAccess, accessView, makeRefresh, rotateRefresh, revokeRefresh,
  };
}
