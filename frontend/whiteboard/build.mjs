import esbuild from 'esbuild';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outFiles = [
  path.join(__dirname, '..', 'dist', 'whiteboard.bundle.js'),
  path.join(__dirname, '..', 'whiteboard.bundle.js'),
];

for (const outfile of outFiles) {
  fs.mkdirSync(path.dirname(outfile), { recursive: true });
  await esbuild.build({
    entryPoints: [path.join(__dirname, 'src', 'main.jsx')],
    outfile,
    bundle: true,
    format: 'iife',
    globalName: 'BervinovWhiteboardBundle',
    platform: 'browser',
    target: ['es2020'],
    jsx: 'automatic',
    loader: {
      '.css': 'css',
    },
    minify: true,
    sourcemap: true,
    define: {
      'process.env.NODE_ENV': '"production"',
    },
  });
}

const assetDirs = ['fonts', 'icons', 'embed-icons', 'translations'];
const assetSrc = path.join(__dirname, 'node_modules', '@tldraw', 'assets');
const assetTargets = [
  path.join(__dirname, '..', 'dist', 'tldraw-assets'),
  path.join(__dirname, '..', 'tldraw-assets'),
];

for (const target of assetTargets) {
  fs.rmSync(target, { recursive: true, force: true });
  fs.mkdirSync(target, { recursive: true });
  for (const dir of assetDirs) {
    const from = path.join(assetSrc, dir);
    if (!fs.existsSync(from)) {
      console.error(`Missing tldraw assets: ${from}`);
      process.exit(1);
    }
    fs.cpSync(from, path.join(target, dir), { recursive: true });
  }
}

console.log('Built whiteboard bundle -> frontend/dist/ and frontend/whiteboard.bundle.js');
console.log('Copied tldraw assets -> /tldraw-assets/ (same origin as the site)');
