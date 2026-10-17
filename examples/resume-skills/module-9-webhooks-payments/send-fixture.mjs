import { fixtureEvent, endpoints } from './fixtures.mjs';
import { sign } from './webhook.mjs';
const raw = Buffer.from(JSON.stringify(fixtureEvent()));
const response = await fetch('http://127.0.0.1:3109/webhooks/alpha', {
  method: 'POST', headers: {
    'Content-Type': 'application/json',
    'X-Razorpay-Signature': sign(raw, endpoints.alpha.secrets[0]),
    'X-Razorpay-Event-Id': 'manual-event-1',
  }, body: raw, signal: AbortSignal.timeout(4000),
});
console.log(response.status, await response.json());
