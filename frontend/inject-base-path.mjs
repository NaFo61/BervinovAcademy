import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const subPath = (process.env.SUB_PATH ?? "").replace(/\/$/, "");
const whiteboardEnabled = process.env.ENABLE_WHITEBOARD !== "false";
const distDir = path.join(__dirname, "dist");
const indexPath = path.join(distDir, "index.html");

if (!fs.existsSync(indexPath)) {
  console.error("dist/index.html not found — run build-dist.mjs first");
  process.exit(1);
}

let html = fs.readFileSync(indexPath, "utf8");
html = html.replace(
  '<meta name="app-base" content="" />',
  `<meta name="app-base" content="${subPath}" />\n<meta name="whiteboard-enabled" content="${whiteboardEnabled ? "true" : "false"}" />`,
);

if (!whiteboardEnabled) {
  html = html.replace(
    /<!-- WHITEBOARD_ASSETS_START -->[\s\S]*?<!-- WHITEBOARD_ASSETS_END -->\n?/,
    "",
  );
}

fs.writeFileSync(indexPath, html);
console.log(
  `Injected app-base=${subPath}, whiteboard=${whiteboardEnabled} into index.html`,
);
