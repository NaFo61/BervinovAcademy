import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = __dirname;
const dist = path.join(root, "dist");
const enableWhiteboard = process.env.ENABLE_WHITEBOARD !== "false";

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
copy("src", "src");
copy("public", "public");

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
