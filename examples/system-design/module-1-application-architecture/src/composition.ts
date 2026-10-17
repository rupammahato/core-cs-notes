import { NotesService } from './notes.js';
import { SqliteNotes } from './sqlite.js';
import { createApp } from './http.js';

export function compose(path: string) {
  const repository = new SqliteNotes(path);
  const service = new NotesService(repository);
  const app = createApp(service);
  return { app, service, close: () => repository.close() };
}
