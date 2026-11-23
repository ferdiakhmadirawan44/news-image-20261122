// main.ts — entrypoint for make.fun bounty news-image-20261122.
//
// The image itself is rendered in code by build.py (Pillow, run locally:
// python3 build.py) and shipped here as entry.png. This program does the
// one thing the sandbox allows — it copies that image to the output
// directory, byte for byte, with nothing but the Node standard library.
// It takes no input, reads no network, and writes the same bytes on
// every run.
//
// Run locally:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, "entry.png");
const targetDir = process.env.MAKEFUN_OUTPUT_DIR || "/output";
const target = join(targetDir, "entry.png");

if (!existsSync(source)) {
  throw new Error("entry.png is missing next to main.ts");
}
mkdirSync(targetDir, { recursive: true });
copyFileSync(source, target);
