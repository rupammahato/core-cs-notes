export function parseMessage(value: unknown): string | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const record = value as Record<string, unknown>;
  if (Object.keys(record).length !== 1 || typeof record.message !== 'string') return null;
  const message = record.message.trim();
  return message.length >= 1 && message.length <= 80 ? message : null;
}
