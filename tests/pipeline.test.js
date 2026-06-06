import test from "node:test";
import assert from "node:assert/strict";

import {
  buildScenePlans,
  buildScenePrompt,
  generateImageMetadata,
  getGeoPreset,
  slugify
} from "../src/shared/pipeline.js";

test("buildScenePlans returns the requested scene count across pipeline categories", () => {
  const plans = buildScenePlans({
    count: 10,
    targetGeo: "SG",
    category: "drinkware",
    brandTone: "premium calm",
    audience: "urban professionals"
  });

  assert.equal(plans.length, 10);
  assert.deepEqual(
    [...new Set(plans.map((plan) => plan.category))],
    ["Lifestyle", "Seasonal", "Use-case", "Geo-variant"]
  );
  assert.equal(plans[0].geo.code, "SG");
  assert.equal(plans[0].dimensions.square, "1200x1200");
});

test("buildScenePrompt includes geo, seasonal, product, and brand constraints", () => {
  const [plan] = buildScenePlans({
    count: 1,
    targetGeo: "PH",
    category: "skincare",
    brandTone: "bright friendly",
    audience: "Gen Z shoppers"
  });

  const prompt = buildScenePrompt(plan);

  assert.match(prompt, /Philippines/i);
  assert.match(prompt, /tropical/i);
  assert.match(prompt, /skincare/i);
  assert.match(prompt, /bright friendly/i);
  assert.match(prompt, /Gen Z shoppers/i);
  assert.match(prompt, /1200x1200/i);
});

test("buildScenePrompt preserves the uploaded product for Shopee previews", () => {
  const [plan] = buildScenePlans({
    count: 1,
    targetGeo: "SG",
    category: "snack pouch",
    brandTone: "clean trustworthy",
    audience: "Shopee shoppers"
  });

  const prompt = buildScenePrompt(plan);

  assert.match(prompt, /Shopee/i);
  assert.match(prompt, /preserve the exact uploaded product/i);
  assert.match(prompt, /do not redesign/i);
  assert.match(prompt, /do not invent/i);
});

test("generateImageMetadata creates marketplace-ready fields", () => {
  const [plan] = buildScenePlans({
    count: 1,
    targetGeo: "IN",
    category: "gift box",
    brandTone: "festive premium",
    audience: "family shoppers"
  });

  const metadata = generateImageMetadata(plan, {
    productName: "Glow Ritual Set",
    targetGeo: "IN"
  });

  assert.equal(metadata.id, plan.id);
  assert.equal(metadata.sceneType, plan.sceneType);
  assert.equal(metadata.geo.market, "India");
  assert.ok(metadata.altText.includes("Glow Ritual Set"));
  assert.ok(metadata.seoTags.length >= 5);
  assert.ok(metadata.tiktokHashtags.some((tag) => tag.startsWith("#")));
  assert.ok(metadata.platformTemplates.shopee.imageSize.includes("1200"));
});

test("getGeoPreset falls back to Southeast Asia when market is unknown", () => {
  assert.equal(getGeoPreset("XX").region, "Southeast Asia");
});

test("slugify produces stable lowercase filenames", () => {
  assert.equal(slugify("Glow Ritual Set: SG Urban!"), "glow-ritual-set-sg-urban");
});
