import { randomBytes, scrypt as scryptCallback, timingSafeEqual } from 'node:crypto';
import { promisify } from 'node:util';

const scrypt = promisify(scryptCallback);
const cost = { N: 131072, r: 8, p: 1, maxmem: 256 * 1024 * 1024 };

function passwordBytes(password) {
  if (typeof password !== 'string' || Buffer.byteLength(password, 'utf8') < 1 ||
      Buffer.byteLength(password, 'utf8') > 256) throw new TypeError('Unsupported password input.');
  return password;
}
export async function hashPassword(password) {
  const salt = randomBytes(16).toString('hex');
  const derived = await scrypt(passwordBytes(password), salt, 64, cost);
  return { scheme: 'scrypt-demo-v1', salt, derived: derived.toString('hex') };
}
export async function verifyPassword(password, record) {
  if (record?.scheme !== 'scrypt-demo-v1' || !/^[a-f0-9]{32}$/.test(record.salt) ||
      !/^[a-f0-9]{128}$/.test(record.derived)) throw new TypeError('Invalid stored credential.');
  const derived = await scrypt(passwordBytes(password), record.salt, 64, cost);
  return timingSafeEqual(derived, Buffer.from(record.derived, 'hex'));
}
