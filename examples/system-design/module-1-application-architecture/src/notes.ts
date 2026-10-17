import { Buffer } from 'node:buffer';

export type Principal = Readonly<{ tenant: string; owner: string }>;
export type Payload = Readonly<{ title: string; content: string }>;
export type Note = Payload & { id: string; revision: number };
export type CreateResult = { note: Note; replayed: boolean };
export type Trace = (event: string) => void;
export class RuleError extends Error {
  constructor(public readonly code: 'invalid' | 'missing' | 'conflict' | 'stale') {
    super(code);
  }
}
export function identity(...values: unknown[]): void {
  if (!values.every(value => typeof value === 'string' && value.length >= 1 && value.length <= 64 && !/[^A-Za-z0-9_-]/.test(value))) {
    throw new RuleError('invalid');
  }
}
export function payload(value: unknown): Payload {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) throw new RuleError('invalid');
  const item = value as Record<string, unknown>;
  if (Object.keys(item).sort().join(',') !== 'content,title' || typeof item.title !== 'string' ||
      item.title.trim().length === 0 || item.title.includes('\0') || [...item.title].length > 120 ||
      typeof item.content !== 'string' || Buffer.byteLength(item.content, 'utf8') > 4096) {
    throw new RuleError('invalid');
  }
  return { title: item.title, content: item.content };
}
export interface NotesRepository {
  create(who: Principal, operation: string, input: Payload, trace: Trace): CreateResult;
  get(who: Principal, id: string, trace: Trace): Note;
  replace(who: Principal, id: string, revision: number, input: Payload, trace: Trace): Note;
}
export class NotesService {
  constructor(private readonly repository: NotesRepository) {}
  create(who: Principal, operation: string, input: unknown, trace: Trace = () => {}): CreateResult {
    identity(who.tenant, who.owner, operation);
    const validated = payload(input);
    trace('service.create.validated');
    return this.repository.create(who, operation, validated, trace);
  }
  get(who: Principal, id: string, trace: Trace = () => {}): Note {
    identity(who.tenant, who.owner, id);
    trace('service.get.validated');
    return this.repository.get(who, id, trace);
  }
  replace(who: Principal, id: string, revision: number, input: unknown, trace: Trace = () => {}): Note {
    identity(who.tenant, who.owner, id);
    if (!Number.isSafeInteger(revision) || revision < 1) throw new RuleError('invalid');
    const validated = payload(input);
    trace('service.replace.validated');
    return this.repository.replace(who, id, revision, validated, trace);
  }
}
