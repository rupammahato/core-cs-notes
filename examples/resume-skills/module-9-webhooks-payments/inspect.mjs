import { fileURLToPath } from 'node:url';
import { openStore } from './store.mjs';
const store = openStore(fileURLToPath(new URL('./demo.sqlite', import.meta.url)));
try { console.log(JSON.stringify(store.snapshot(), null, 2)); } finally { store.close(); }
