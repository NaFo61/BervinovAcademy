import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';

const DIR = resolve(process.env.DATA_DIR || './data', 'assets');

/** Max bytes for in-sync assets (images only). Larger files go via Django board-assets. */
export const MAX_ASSET_BYTES = Number(
  process.env.WHITEBOARD_SYNC_MAX_ASSET_BYTES || 2 * 1024 * 1024,
);

export class AssetTooLargeError extends Error {
  constructor(size) {
    super(`Asset too large: ${size} bytes`);
    this.name = 'AssetTooLargeError';
    this.size = size;
  }
}

export async function storeAsset(id, stream) {
  await mkdir(DIR, { recursive: true });
  const chunks = [];
  let total = 0;
  for await (const chunk of stream) {
    total += chunk.length;
    if (total > MAX_ASSET_BYTES) {
      throw new AssetTooLargeError(total);
    }
    chunks.push(chunk);
  }
  await writeFile(join(DIR, id), Buffer.concat(chunks));
}

export async function loadAsset(id) {
  return readFile(join(DIR, id));
}
