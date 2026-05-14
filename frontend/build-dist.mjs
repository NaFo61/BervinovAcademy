import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = __dirname;
const dist = path.join(root, "dist");

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
