import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';

const DIR = resolve(process.env.DATA_DIR || './data', 'assets');

export async function storeAsset(id, stream) {
  await mkdir(DIR, { recursive: true });
  const chunks = [];
  for await (const chunk of stream) {
    chunks.push(chunk);
  }
  await writeFile(join(DIR, id), Buffer.concat(chunks));
}

export async function loadAsset(id) {
  return readFile(join(DIR, id));
}
