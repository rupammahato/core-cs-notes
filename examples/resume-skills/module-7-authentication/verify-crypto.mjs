import { randomBytes, hkdfSync } from 'node:crypto';
import { SignJWT, decodeJwt, generateKeyPair, EncryptJWT, jwtDecrypt } from 'jose';
import { hashPassword, verifyPassword } from './password.mjs';
import { createIdentity } from './identity.mjs';
import { assert, check, rejected, save } from './checks.mjs';

const password = 'placement-demo-password';
const credential = await hashPassword(password);
const otherCredential = await hashPassword(password);
await check('same password receives independent random salts', async () => {
  assert.notEqual(credential.salt, otherCredential.salt);
  assert.notEqual(credential.derived, otherCredential.derived);
  return { saltsDiffer: true, derivedValuesDiffer: true };
});
await check('correct password verifies', async () => {
  assert.equal(await verifyPassword(password, credential), true); return true;
});
await check('wrong password fails', async () => {
  assert.equal(await verifyPassword('incorrect-demo-password', credential), false); return false;
});
await check('password whitespace is not silently trimmed', async () => {
  assert.equal(await verifyPassword(' ' + password, credential), false); return false;
});
await check('oversize password rejected before derivation', async () =>
  rejected(() => verifyPassword('x'.repeat(257), credential), 'Unsupported password input.'));
await check('invalid stored hash format rejected', async () =>
  rejected(() => verifyPassword(password, { ...credential, derived: 'bad' }), 'Invalid stored credential.'));

let clock = 1_000_000;
const keys = await generateKeyPair('RS256');
const identity = await createIdentity({ passwordRecord: credential, now: () => clock, keyPair: keys });
const subject = 'user-1';
const token = await identity.issueAccess(subject);
await check('signed JWT has three parts and readable untrusted claims', async () => {
  assert.equal(token.split('.').length, 3);
  const decoded = decodeJwt(token);
  assert.equal(decoded.sub, subject);
  assert.equal(Object.hasOwn(decoded, 'password'), false);
  return { parts: 3, decodedSubject: decoded.sub, containsPassword: false };
});
await check('signature and expected claims permit valid access', async () => {
  assert.equal((await identity.accessView(token)).user.id, subject); return { subject };
});
const claims = {
  iss: 'https://identity.example.test', aud: 'placement-api', sub: subject,
  iat: 1000, exp: 1060, jti: 'demo-jti',
};
async function signed(overrides = {}, header = {}) {
  return new SignJWT({ ...claims, ...overrides }).setProtectedHeader({
    alg: 'RS256', typ: 'at+jwt', kid: 'demo-rsa-1', ...header,
  }).sign(keys.privateKey);
}
await check('payload tampering is rejected even though decoding succeeds', async () => {
  const parts = token.split('.');
  parts[1] = Buffer.from(JSON.stringify({ ...decodeJwt(token), sub: 'attacker' })).toString('base64url');
  const changed = parts.join('.');
  assert.equal(decodeJwt(changed).sub, 'attacker');
  return rejected(() => identity.accessView(changed), 'invalid_access_token');
});
for (const [name, overrides, header] of [
  ['wrong issuer', { iss: 'https://attacker.example.test' }, {}],
  ['wrong audience', { aud: 'another-api' }, {}],
  ['expired token', { exp: 1000 }, {}],
  ['not-yet-valid token', { nbf: 1001 }, {}],
  ['missing expiry', { exp: undefined }, {}],
  ['missing subject', { sub: undefined }, {}],
  ['future issued-at', { iat: 1001 }, {}],
  ['oversize lifetime', { exp: 1061 }, {}],
  ['wrong token purpose', {}, { typ: 'JWT' }],
  ['unexpected key ID', {}, { kid: 'unknown' }],
]) await check(name + ' rejected', async () => rejected(() =>
  signed(overrides, header).then(value => identity.accessView(value)), 'invalid_access_token'));
await check('wrong signing key rejected', async () => {
  const wrongKeys = await generateKeyPair('RS256');
  const wrong = await new SignJWT(claims).setProtectedHeader({ alg: 'RS256', typ: 'at+jwt', kid: 'demo-rsa-1' }).sign(wrongKeys.privateKey);
  return rejected(() => identity.accessView(wrong), 'invalid_access_token');
});
await check('unsecured alg none rejected', async () => {
  const value = Buffer.from(JSON.stringify({ alg: 'none', typ: 'at+jwt' })).toString('base64url') + '.' +
    Buffer.from(JSON.stringify(claims)).toString('base64url') + '.';
  return rejected(() => identity.accessView(value), 'invalid_access_token');
});
await check('HS256 rejected by RS256 allowlist', async () => {
  const value = await new SignJWT(claims).setProtectedHeader({ alg: 'HS256', typ: 'at+jwt' }).sign(randomBytes(32));
  return rejected(() => identity.accessView(value), 'invalid_access_token');
});
clock = 1_059_999;
await check('access valid immediately before expiry', async () => {
  assert.equal((await identity.accessView(token)).user.id, subject); return { atMs: clock, valid: true };
});
clock = 1_060_000;
await check('access invalid exactly at expiry', async () =>
  rejected(() => identity.accessView(token), 'invalid_access_token'));

clock = 2_000_000;
const session1 = identity.makeSession(subject);
const session2 = identity.makeSession(subject, session1.token);
await check('re-login replaces previous session credential', async () => {
  assert.notEqual(session1.token, session2.token);
  await rejected(async () => identity.sessionView(session1.token), 'unauthenticated');
  assert.equal(identity.sessionView(session2.token).user.id, subject);
  return { previousValid: false, currentValid: true };
});
clock += 29_999;
await check('accepted session activity renews idle clock', async () => {
  assert.equal(identity.sessionView(session2.token).user.id, subject); return { elapsedMs: 29999 };
});
clock += 30_000;
await check('idle timeout rejects at boundary', async () =>
  rejected(async () => identity.sessionView(session2.token), 'session_expired'));

clock = 3_000_000;
const absolute = identity.makeSession(subject);
for (let elapsed = 20_000; elapsed < 120_000; elapsed += 20_000) {
  clock = 3_000_000 + elapsed; identity.sessionView(absolute.token);
}
clock = 3_120_000;
await check('absolute timeout survives continued activity', async () =>
  rejected(async () => identity.sessionView(absolute.token), 'session_expired'));
clock = 4_000_000;
const csrfSession = identity.makeSession(subject);
await check('wrong CSRF token leaves session usable', async () => {
  await rejected(async () => identity.logoutSession(csrfSession.token, 'wrong'), 'csrf_rejected');
  assert.equal(identity.sessionView(csrfSession.token).user.id, subject);
  return { rejected: 'csrf_rejected', sessionStillValid: true };
});
await check('logout revokes server-side session', async () => {
  identity.logoutSession(csrfSession.token, csrfSession.csrf);
  return rejected(async () => identity.sessionView(csrfSession.token), 'unauthenticated');
});

clock = 5_000_000;
const firstRefresh = identity.makeRefresh(subject);
const nextRefresh = identity.rotateRefresh(firstRefresh);
await check('refresh rotation issues a distinct successor', async () => {
  assert.notEqual(firstRefresh, nextRefresh.refreshToken);
  assert.equal(nextRefresh.subject, subject); return { distinct: true, subject };
});
await check('reuse of consumed refresh revokes family', async () => {
  await rejected(async () => identity.rotateRefresh(firstRefresh), 'refresh_reuse');
  await rejected(async () => identity.rotateRefresh(nextRefresh.refreshToken), 'invalid_refresh_token');
  return { reuseRejected: true, successorRejected: true };
});
await check('unknown refresh does not revoke unrelated family', async () => {
  const separate = identity.makeRefresh(subject);
  await rejected(async () => identity.rotateRefresh('x'.repeat(43)), 'invalid_refresh_token');
  assert.equal(identity.rotateRefresh(separate).subject, subject);
  return { unrelatedFamilyValid: true };
});
const expiredRefresh = identity.makeRefresh(subject);
clock += 299_999;
const lateSuccessor = identity.rotateRefresh(expiredRefresh).refreshToken;
clock += 1;
await check('refresh family expires at fixed absolute boundary', async () =>
  rejected(async () => identity.rotateRefresh(lateSuccessor), 'invalid_refresh_token'));

const encryptionKey = randomBytes(32);
const encrypted = await new EncryptJWT({ note: 'private-demo-value' })
  .setProtectedHeader({ alg: 'dir', enc: 'A256GCM' }).setIssuedAt(1000).setExpirationTime(1060)
  .encrypt(encryptionKey);
await check('JWE has five parts and decrypts with expected algorithms', async () => {
  assert.equal(encrypted.split('.').length, 5);
  const { payload } = await jwtDecrypt(encrypted, encryptionKey, {
    keyManagementAlgorithms: ['dir'], contentEncryptionAlgorithms: ['A256GCM'], currentDate: new Date(1_030_000),
  });
  assert.equal(payload.note, 'private-demo-value');
  return { parts: 5, decryptedNote: payload.note };
});
await check('JWE rejects wrong decryption key', async () => {
  await assert.rejects(() => jwtDecrypt(encrypted, randomBytes(32), { currentDate: new Date(1_030_000) }));
  return { rejected: true };
});
await check('JWE still enforces expiry', async () => {
  await assert.rejects(() => jwtDecrypt(encrypted, encryptionKey, { currentDate: new Date(1_060_000) }));
  return { rejected: true };
});
await check('HKDF context separates derived keys', async () => {
  const input = randomBytes(32), salt = randomBytes(16);
  const derive = info => Buffer.from(hkdfSync('sha256', input, salt, info, 32));
  assert.deepEqual(derive('placement-session'), derive('placement-session'));
  assert.notDeepEqual(derive('placement-session'), derive('placement-other-purpose'));
  return { sameContextSameKey: true, changedContextDifferentKey: true, bytes: 32 };
});
await save('crypto');
