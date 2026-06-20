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

console.log('Built whiteboard bundle -> frontend/dist/ and frontend/whiteboard.bundle.js');
