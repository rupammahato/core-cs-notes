import { build } from 'esbuild';
import { mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
await mkdir(new URL('./dist/', import.meta.url), { recursive: true });
for (const mode of ['development', 'production']) {
  await build({ entryPoints: [fileURLToPath(new URL('./main.jsx', import.meta.url))],
    bundle: true, outfile: fileURLToPath(new URL('./dist/app.' + mode + '.js', import.meta.url)),
    format: 'iife', jsx: 'automatic', minify: mode === 'production',
    define: { 'process.env.NODE_ENV': JSON.stringify(mode) }, logLevel: 'info' });
}
