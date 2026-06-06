import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";

const apiRoutes = [
  "api/health.py",
  "api/categories.py",
  "api/remove-background.py",
  "api/generate-scene.py",
  "api/generate-listing-draft.py"
];

test("Vercel API routes expose the Python app endpoints", () => {
  for (const route of apiRoutes) {
    assert.equal(existsSync(route), true, `${route} should exist`);
    assert.match(
      readFileSync(route, "utf8"),
      /ScenarioRequestHandler as handler/,
      `${route} should delegate to the shared Python handler`
    );
    assert.match(
      readFileSync(route, "utf8"),
      /sys\.path\.insert/,
      `${route} should make the repo root importable`
    );
  }
});
