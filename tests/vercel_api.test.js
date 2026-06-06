import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";

const apiRoutes = [
  "api/health.py",
  "api/categories.py",
  "api/template-fields.py",
  "api/remove-background.py",
  "api/generate-scene.py",
  "api/generate-listing-draft.py",
  "api/export-template-xlsx.py",
  "api/map-template-row.py"
];

test("Vercel API routes expose the Python app endpoints", () => {
  for (const route of apiRoutes) {
    assert.equal(existsSync(route), true, `${route} should exist`);
    assert.match(
      readFileSync(route, "utf8"),
      /class handler\(ScenarioRequestHandler\):/,
      `${route} should define Vercel's expected handler class`
    );
    assert.match(
      readFileSync(route, "utf8"),
      /sys\.path\.insert/,
      `${route} should make the repo root importable`
    );
  }
});

test("Vercel config registers Python API routes before static output", () => {
  const config = JSON.parse(readFileSync("vercel.json", "utf8"));

  assert.deepEqual(config.builds?.[0], {
    src: "api/*.py",
    use: "@vercel/python"
  });
  assert.deepEqual(config.routes?.[0], {
    src: "/api/(.*)",
    dest: "/api/$1.py"
  });
  assert.deepEqual(config.routes?.[1], {
    src: "/",
    dest: "/index.html"
  });
  assert.deepEqual(config.routes?.[2], {
    src: "/(.*)",
    dest: "/$1"
  });
});
