import test from "node:test";
import assert from "node:assert/strict";

import { createZipBytes } from "../src/shared/zip.js";

test("createZipBytes writes a valid store-only zip structure", () => {
  const zip = createZipBytes([
    { name: "metadata.json", data: "{\"ok\":true}" },
    { name: "images/product.png", data: new Uint8Array([137, 80, 78, 71]) }
  ]);

  assert.equal(zip[0], 0x50);
  assert.equal(zip[1], 0x4b);
  assert.equal(zip[2], 0x03);
  assert.equal(zip[3], 0x04);

  const text = new TextDecoder().decode(zip);
  assert.ok(text.includes("metadata.json"));
  assert.ok(text.includes("images/product.png"));
  assert.ok(text.includes("PK\u0001\u0002"));
  assert.ok(text.includes("PK\u0005\u0006"));
});
