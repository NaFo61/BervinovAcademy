import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = __dirname;
const dist = path.join(root, "dist");
const enableWhiteboard = process.env.ENABLE_WHITEBOARD !== "false";

const cssBin = process.platform === "win32" ? "npx.cmd" : "npx";
const css = spawnSync(
  cssBin,
  [
    "--yes",
    "tailwindcss@3.4.17",
    "-i",
    "./src/tailwind-input.css",
    "-o",
    "./tailwind.css",
    "--minify",
  ],
  {
    cwd: root,
    stdio: "inherit",
    shell: process.platform === "win32",
  },
);
if (css.status !== 0) {
  const existing = path.join(root, "tailwind.css");
  if (!fs.existsSync(existing)) {
    console.error("tailwind.css missing and CLI build failed");
    process.exit(css.status ?? 1);
  }
  console.warn("Tailwind CLI unavailable; using committed tailwind.css");
}

fs.rmSync(dist, { recursive: true, force: true });
fs.mkdirSync(dist, { recursive: true });

const copy = (from, to) => {
  const absFrom = path.join(root, from);
  if (!fs.existsSync(absFrom)) return;
  const absTo = path.join(dist, to);
  const st = fs.statSync(absFrom);
  if (st.isDirectory()) {
    fs.cpSync(absFrom, absTo, { recursive: true });
  } else {
    fs.copyFileSync(absFrom, absTo);
  }
};

copy("index.html", "index.html");
copy("tailwind.css", "tailwind.css");
copy("src", "src");
copy("public", "public");
copy("icons", "icons");
copy("img", "img");
copy("sw.js", "sw.js");

if (enableWhiteboard) {
  const whiteboardDir = path.join(root, "whiteboard");
  const whiteboardBuild = spawnSync(
    process.platform === "win32" ? "npm.cmd" : "npm",
    ["run", "build"],
    {
      cwd: whiteboardDir,
      stdio: "inherit",
      shell: process.platform === "win32",
    },
  );
  if (whiteboardBuild.status !== 0) {
    process.exit(whiteboardBuild.status ?? 1);
  }
} else {
  console.log("Whiteboard build skipped (ENABLE_WHITEBOARD=false)");
}
