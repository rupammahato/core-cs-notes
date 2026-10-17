export const endpoints = {
  alpha: { accountId: 'acc_alpha', secrets: ['alpha-demo-secret', 'alpha-old-demo-secret'] },
  beta: { accountId: 'acc_beta', secrets: ['beta-demo-secret'] },
};
export const orders = [
  { tenant: 'alpha', localId: 'a-1', endpoint: 'alpha', providerId: 'order_alpha_1', amount: 25000, currency: 'INR', credits: 100 },
  { tenant: 'alpha', localId: 'a-2', endpoint: 'alpha', providerId: 'order_alpha_2', amount: 50000, currency: 'INR', credits: 200 },
  { tenant: 'beta', localId: 'b-1', endpoint: 'beta', providerId: 'order_beta_1', amount: 25000, currency: 'INR', credits: 100 },
];
export function fixtureEvent({
  endpoint = 'alpha', type = 'payment.captured', paymentId = 'pay_alpha_1',
  providerOrderId = endpoint === 'alpha' ? 'order_alpha_1' : 'order_beta_1',
  amount = 25000, currency = 'INR', extra = {},
} = {}) {
  return {
    entity: 'event', account_id: 'acc_' + endpoint, event: type,
    payload: { payment: { entity: {
      entity: 'payment', id: paymentId, order_id: providerOrderId, amount, currency,
      status: type.split('.')[1],
    } } }, ...extra,
  };
}
