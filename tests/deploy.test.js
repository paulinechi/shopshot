import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import test from "node:test";

test("static build publishes shared browser modules used by app.js", () => {
  rmSync("public/src", { recursive: true, force: true });

  execFileSync("npm", ["run", "build"], { stdio: "pipe" });

  assert.equal(
    readFileSync("public/src/shared/pipeline.js", "utf8"),
    readFileSync("src/shared/pipeline.js", "utf8")
  );
  assert.equal(
    readFileSync("public/src/shared/zip.js", "utf8"),
    readFileSync("src/shared/zip.js", "utf8")
  );
});
