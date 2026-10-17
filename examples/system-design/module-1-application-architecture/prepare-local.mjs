import { mkdir, symlink, realpath, access } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

// Reuse installed packages without downloading or modifying the original directories.
const base = path.dirname(fileURLToPath(import.meta.url));
await mkdir(path.join(base, 'node_modules'), { recursive: true });
const links = {
  express: '../../resume-skills/module-5-express/node_modules/express',
  '@types': '../../resume-skills/module-5-express/node_modules/@types',
  'undici-types': '../../resume-skills/module-5-express/node_modules/undici-types',
  typescript: '../../../study-guide/node_modules/typescript',
  acorn: '../../../study-guide/node_modules/acorn',
};
for (const [name, relative] of Object.entries(links)) {
  const source = await realpath(path.resolve(base, relative));
  const target = path.join(base, 'node_modules', name);
  try { await access(target); }
  catch (error) {
    if (error.code !== 'ENOENT') throw error;
    await symlink(source, target, process.platform === 'win32' ? 'junction' : 'dir');
  }
  if (await realpath(target) !== source) throw new Error('Unexpected existing dependency: ' + name);
}
console.log('Local dependency links ready; source installations unchanged.');
