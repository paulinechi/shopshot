import { cpSync, mkdirSync, rmSync } from "node:fs";

const outputSharedDir = "public/src/shared";

rmSync(outputSharedDir, { recursive: true, force: true });
mkdirSync(outputSharedDir, { recursive: true });

cpSync("src/shared/pipeline.js", `${outputSharedDir}/pipeline.js`);
cpSync("src/shared/zip.js", `${outputSharedDir}/zip.js`);
