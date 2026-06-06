const GEO_PRESETS = {
  SEA: {
    code: "SEA",
    market: "Southeast Asia",
    region: "Southeast Asia",
    aesthetic: "warm tropical daylight, compact city apartments, lush greenery, marketplace-friendly styling",
    seasonalMarkers: ["monsoon freshness", "humid summer light", "festival gifting", "urban balcony greenery"],
    culturalMarkers: ["modest casual clothing", "shared meals", "mobile-first shopping cues"],
    colorNotes: "fresh greens, coral accents, warm neutrals"
  },
  SG: {
    code: "SG",
    market: "Singapore",
    region: "Southeast Asia",
    aesthetic: "clean urban apartment, HDB and condo lifestyle cues, modern city greenery, polished retail lighting",
    seasonalMarkers: ["year-round summer", "rain-ready monsoon details", "Lunar New Year gifting", "National Day accents"],
    culturalMarkers: ["multicultural dining table", "neat compact storage", "commuter workday routines"],
    colorNotes: "jade green, soft red accents, concrete neutrals, daylight white"
  },
  PH: {
    code: "PH",
    market: "Philippines",
    region: "Southeast Asia",
    aesthetic: "tropical home, bright natural light, palm textures, casual family lifestyle, warm social energy",
    seasonalMarkers: ["sunny summer", "rainy season", "holiday gifting", "beach weekend cues"],
    culturalMarkers: ["family dining", "woven textures", "light casual clothing"],
    colorNotes: "mango yellow, palm green, sky blue, warm white"
  },
  IN: {
    code: "IN",
    market: "India",
    region: "South Asia",
    aesthetic: "rich home textures, festive retail styling, warm indoor light, colorful but premium composition",
    seasonalMarkers: ["summer heat", "monsoon freshness", "winter gifting", "Diwali-inspired festive glow"],
    culturalMarkers: ["brass accents", "rangoli-inspired patterns", "gift-ready presentation"],
    colorNotes: "saffron, marigold, teal, ivory, warm gold"
  },
  US: {
    code: "US",
    market: "United States",
    region: "Western",
    aesthetic: "bright editorial lifestyle, suburban home and studio settings, clean DTC product photography",
    seasonalMarkers: ["summer outdoor use", "fall gifting", "winter cozy interior", "holiday packaging"],
    culturalMarkers: ["minimal home decor", "commuter work setup", "gift wrap and unboxing cues"],
    colorNotes: "navy, sage, white, graphite, seasonal accent colors"
  }
};

const SCENE_CATALOG = [
  ["Lifestyle", "home", "styled on a tidy home surface with everyday context"],
  ["Lifestyle", "work", "placed in a focused desk or workday environment"],
  ["Lifestyle", "outdoor", "shown outdoors with natural regional light"],
  ["Lifestyle", "travel", "packed or carried for a short trip"],
  ["Lifestyle", "dining", "integrated into a meal or cafe moment"],
  ["Lifestyle", "leisure", "shown during a relaxed weekend activity"],
  ["Seasonal", "summer", "adapted for warm-weather seasonal demand"],
  ["Seasonal", "monsoon", "styled with rain-season freshness and practical cues"],
  ["Seasonal", "winter", "styled for cozy gifting and cooler-season shopping"],
  ["Seasonal", "festival", "styled with market-appropriate festive markers"],
  ["Use-case", "product detail", "close-up detail scene emphasizing texture and key features"],
  ["Use-case", "hands-on", "shown being held or used naturally"],
  ["Use-case", "scale", "shown with familiar objects to communicate size"],
  ["Use-case", "gift packaging", "styled as a gift or premium unboxing moment"],
  ["Geo-variant", "southeast asia", "regional Southeast Asian visual language"],
  ["Geo-variant", "south asia", "regional South Asian visual language"],
  ["Geo-variant", "western", "regional Western marketplace visual language"]
];

export function getGeoPreset(targetGeo = "SEA") {
  return GEO_PRESETS[String(targetGeo).trim().toUpperCase()] ?? GEO_PRESETS.SEA;
}

export function slugify(value) {
  return String(value)
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function buildScenePlans(input = {}) {
  const count = clamp(Number(input.count) || 8, 1, 10);
  const geo = getGeoPreset(input.targetGeo);
  const productName = clean(input.productName || "Product");
  const category = clean(input.category || "general product");
  const brandTone = clean(input.brandTone || "marketplace-ready");
  const audience = clean(input.audience || "online shoppers");
  const selectedScenes = selectBalancedScenes(count);

  return selectedScenes.map(([categoryName, sceneType, description], index) => ({
    id: `${String(index + 1).padStart(2, "0")}-${slugify(sceneType)}`,
    index: index + 1,
    category: categoryName,
    sceneType,
    description,
    productName,
    productCategory: category,
    brandTone,
    audience,
    geo,
    dimensions: {
      square: "1200x1200",
      shopee: "1200x1200",
      lazada: "1200x1200",
      tiktokShop: "1200x1200"
    }
  }));
}

export function buildScenePrompt(plan) {
  return [
    `Create a square 1200x1200 Shopee product preview image for ${plan.productName}, a ${plan.productCategory}.`,
    `Use the uploaded product photo as the source of truth: preserve the exact uploaded product shape, color, material, label, logo, text, packaging, proportions, and visible details.`,
    `Do not redesign the product, do not invent new packaging, do not change branding, and do not turn it into a different object.`,
    `Only polish listing presentation: cleaner lighting, sharper edges, natural shadows, tidy marketplace composition, and an appropriate subtle background or context.`,
    `Scene type: ${plan.category} / ${plan.sceneType}. ${plan.description}.`,
    `Target market: ${plan.geo.market}, ${plan.geo.region}. Use ${plan.geo.aesthetic}.`,
    `Seasonal and cultural filters: ${plan.geo.seasonalMarkers.join(", ")}; ${plan.geo.culturalMarkers.join(", ")}.`,
    `Brand tone: ${plan.brandTone}. Audience: ${plan.audience}.`,
    `Visual direction: Shopee listing hero, product remains the clear subject, realistic lighting, no fake logos, no unreadable text, ${plan.geo.colorNotes}.`
  ].join(" ");
}

export function generateImageMetadata(plan, input = {}) {
  const productName = clean(input.productName || plan.productName);
  const baseKeywords = [
    plan.productCategory,
    plan.sceneType,
    plan.geo.market,
    plan.geo.region,
    plan.brandTone,
    "ecommerce product photo",
    "marketplace listing",
    "lifestyle product image"
  ];

  const seoTags = unique(baseKeywords.map(slugify).filter(Boolean)).slice(0, 10);

  return {
    id: plan.id,
    fileBaseName: `${slugify(productName)}-${plan.id}`,
    sceneType: plan.sceneType,
    sceneCategory: plan.category,
    geo: {
      code: plan.geo.code,
      market: plan.geo.market,
      region: plan.geo.region
    },
    keywords: unique(baseKeywords).slice(0, 10),
    seoTags,
    altText: `${productName} shown in a ${plan.sceneType} ${plan.geo.market} product scene for ${plan.audience}.`,
    shopeeDescription: `${productName} styled for ${plan.geo.market} shoppers in a ${plan.sceneType} scene. Designed for ${plan.brandTone} brand positioning and fast marketplace listing creation.`,
    tiktokHashtags: seoTags.slice(0, 6).map((tag) => `#${tag.replace(/-/g, "")}`),
    platformTemplates: {
      shopee: {
        imageSize: plan.dimensions.shopee,
        usage: "Main listing image or variation gallery"
      },
      lazada: {
        imageSize: plan.dimensions.lazada,
        usage: "Product gallery image"
      },
      tiktokShop: {
        imageSize: plan.dimensions.tiktokShop,
        usage: "Product card, short-form commerce creative, or carousel"
      }
    }
  };
}

export function buildGenerationPayload(input = {}) {
  const plans = buildScenePlans(input);
  return {
    plans,
    prompts: plans.map((plan) => ({
      id: plan.id,
      prompt: buildScenePrompt(plan)
    })),
    metadata: plans.map((plan) => generateImageMetadata(plan, input))
  };
}

function clean(value) {
  return String(value).trim().replace(/\s+/g, " ");
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function selectBalancedScenes(count) {
  const byCategory = SCENE_CATALOG.reduce((groups, scene) => {
    const category = scene[0];
    groups.set(category, [...(groups.get(category) || []), scene]);
    return groups;
  }, new Map());

  const selected = [];
  const used = new Set();
  for (const scenes of byCategory.values()) {
    if (selected.length >= count) break;
    selected.push(scenes[0]);
    used.add(scenes[0].join("|"));
  }

  for (const scene of SCENE_CATALOG) {
    if (selected.length >= count) break;
    const key = scene.join("|");
    if (!used.has(key)) {
      selected.push(scene);
      used.add(key);
    }
  }

  return selected;
}
