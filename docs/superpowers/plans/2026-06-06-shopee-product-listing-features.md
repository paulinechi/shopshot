# Shopee Product Listing Features And User Workflow Plan

> **For review before implementation:** This plan defines the product-listing feature scope, user workflow, generated metadata, user-entered fields, readiness scoring, and export behavior. No app code should be changed until this document is reviewed and approved.

**Goal:** Extend the current Shopee Product Preview Polisher into a Shopee listing draft builder that turns uploaded product images into editable listing metadata, readiness warnings, and export-ready JSON while preserving the product image-polishing workflow.

**Architecture:** Keep the current no-install vanilla frontend and Python backend. Add a structured listing layer beside the existing preview image workflow on the same page: image/product understanding, editable listing draft, readiness score, missing-field checklist, and JSON export mapping. AI-generated fields must be marked as detected, inferred, provided, or missing so sellers know what needs review.

**Tech Stack:** Python backend, vanilla HTML/CSS/JS frontend, OpenAI image references/image edits for preview polishing, OpenAI vision/text generation for listing metadata, browser-side JSON export, current Node/Python tests.

---

## Source Notes

Read for this plan:

- `team_docs/PRD_Shopee_MVP.md`, starting from chapter 8 as requested.
- `team_docs/shopee-scene-studio (1) (1).html`, especially upload/settings, metadata editor, tag editor, export JSON, and Shopee push placeholder.

Ignored for planning:

- PRD chapters 1-7.

Relevant PRD product idea:

- Product concept after chapter 7 is **Catalog Copilot / ShopShot**, but this implementation should focus on Shopee listing draft creation and export. Product catalog management is removed because Shopee Seller Platform already supports catalog management.
- Core flow: upload product images, AI generates Shopee product profile, user reviews detected/missing information, AI creates listing, user exports Shopee-ready content.
- Important safety rule: AI must not invent unsupported exact specs, regulated claims, fake discounts, fake urgency, or treat inferred information as confirmed fact.

Additional Shopee category context:

- Shopee categories are a predefined marketplace taxonomy, not free-form text.
- Official source of truth should be Shopee Open Platform `GET /api/v2/product/get_category`.
- The category response is a flat list with fields such as `category_id`, `parent_category_id`, `original_category_name`, and `has_children`; the app should reconstruct this into a tree/path for search and selection.
- Do not build on unofficial Shopee frontend category endpoints such as `shopee.sg/api/v4/pages/get_category_tree`; they can be blocked, changed, or removed without notice.
- For MVP without Shopee OAuth/app approval, use a cached/static category snapshot shaped like the official API response, then swap to live Open Platform sync when credentials are available.

Relevant HTML reference:

- Existing reference has a 4-step UI: upload/settings, generated previews, listing metadata editor, export/push action bar.
- Metadata fields shown in the reference: Shopee listing title, product description, short social blurb, SEO keywords, hashtags, alt text, auto-matched Shopee category.
- Input fields shown in the reference: product name, category, brand tone, price range, target market, scene types, output count.
- Export reference emits JSON with product name, generated timestamp, geos, title, description, social caption, alt text, SEO keywords, hashtags, Shopee category, and selected scene references.

---

## Recommended Scope

Build this as the next MVP layer over the current app:

1. **Product Listing Draft**
   - Generate a structured Shopee listing draft from uploaded product images and optional seller inputs.
   - Draft is editable before export.
   - Draft separates detected, provided, inferred, and missing information.

2. **Seller Review Workspace**
   - Let users edit listing title, category, description, highlights, attributes, price, stock, brand, variations, weight, and dimensions.
   - Let users confirm or reject AI suggestions.
   - Show missing fields and readiness score.

3. **Shopee-Ready Export**
   - Export polished preview images plus listing metadata.
   - Export JSON only for this phase.
   - Include warnings for fields that still need seller review.

Not in this next slice:

- Direct Shopee API publishing.
- Shopee OAuth.
- Official Shopee attribute/template compliance for every category.
- Live Shopee category sync unless API credentials/partner approval are available.
- Account system, persistent database, inventory, orders, pricing automation.
- Product catalog/dashboard features, because Shopee Seller Platform already covers product catalog management.
- SKU collection or SKU export in this phase.
- CSV export.
- Multi-channel outputs beyond optional social caption/hashtags already present in the reference HTML.

---

## Metadata Ownership

The app should not blur generated and user-filled data. Every listing field should have an ownership/status marker.

### AI Should Generate

These can be generated from images, seller notes, and existing inputs:

| Field | Output Type | Confidence Source | Editable | Notes |
|---|---|---|---|---|
| Detected product type | Structured text | Detected | Yes | Example: Backpack, skincare set, snack pouch |
| Suggested Shopee category | Category ID + path | Inferred | Yes | Must map to the Shopee category tree before export |
| Shopee listing title | Text | Generated | Yes | Keyword-friendly, no unsupported claims |
| Product description | Text area | Generated | Yes | Buyer-friendly, based only on detected/provided facts |
| Product highlights | Bullet list | Generated | Yes | 3-6 bullets; separate facts from assumptions |
| SEO keywords | Tags | Generated | Yes | 5-10 keywords |
| Hashtags | Tags | Generated | Yes | Shopee/social-style tags |
| Alt text | Text area | Generated | Yes | Based on final selected preview image |
| Short social blurb | Text area | Generated | Yes | Optional; lower priority than Shopee listing |
| Visible attributes | Key/value list | Detected | Confirm/reject | Color, style, shape, visible components, packaging |
| Suggested attributes | Key/value list | Inferred | Confirm/reject | Use case, audience, category attributes |
| Missing fields | Checklist | Rules + AI | User fills | Used for readiness score |
| Suggested variants | List | Detected/inferred | Yes | Only if images show colors/styles/bundles |
| Readiness suggestions | Checklist | Rules | No direct edit | Example: Add dimensions, add stock |

### User Should Fill In Or Confirm

These should not be treated as confirmed unless the seller provides them:

| Field | Required For Export Status? | Reason |
|---|---:|---|
| Product images | Yes | Required input and listing media |
| Main product image selection | Yes | Seller should choose hero preview |
| Product name/title confirmation | Yes | AI draft must be reviewed |
| Category confirmation | Yes | Shopee category suggestion may be imperfect |
| Price | Yes | AI should not invent price; seller must provide it |
| Stock | Yes | AI should not invent inventory; seller must provide it |
| Brand | Optional unless provided/visible | Do not invent brand |
| Material | Missing until visible/provided | Avoid unsupported material claims |
| Size/dimensions | Missing until provided | Avoid guessing exact measurements |
| Weight | Missing until provided | Needed for real Shopee logistics |
| Warranty | Missing until provided | Do not invent warranty |
| Compatibility | Missing until provided | Example: laptop size support |
| Variation details | Seller confirmed | Color, size, bundle, quantity |
| Care instructions | Optional/provided | Do not invent if product-specific |

### Category Handling Rules

Shopee category must be represented as both ID and display path:

```json
{
  "category_id": 100001,
  "parent_category_id": 0,
  "original_category_name": "Health",
  "display_path": "Health",
  "has_children": true,
  "source": "shopee_open_platform_snapshot",
  "needs_user_review": true
}
```

Rules:

- AI may suggest a category by matching product type and seller hint against the category tree.
- AI must not invent category IDs.
- If no confident match exists, category remains missing and the user must search/select manually.
- Export should include `category_id` when available, plus `category_path` for human review.
- Readiness score should penalize missing or unconfirmed `category_id`.
- Future Shopee API listing creation must use `category_id`, not only category text.

Suggested UX:

- Category field should be a searchable selector backed by the category tree.
- Display category path, not only leaf name.
- Show `AI suggested` beside category until user confirms.
- Allow user to override with another category from the tree.

### Field Status Model

Each important field should carry:

```json
{
  "value": "Black",
  "source": "detected | provided | inferred | missing | confirmed",
  "confidence": "high | medium | low",
  "needs_user_review": true
}
```

This model is important because the PRD repeatedly says the AI must separate detected facts from assumptions.

---

## User Workflow

### Workflow 1: Create Shopee Listing Draft

1. User opens the app.
2. User uploads one or more product images.
3. App shows image thumbnails and product isolation previews.
4. User can remove images and select the main image.
5. User enters seller inputs:
   - product note
   - category hint
   - brand/tone
   - target market
   - price, required for Ready to Export
   - stock, required for Ready to Export
   - stock
6. User clicks `Generate Shopee Listing Draft`.
7. Backend analyzes uploaded images and seller inputs.
8. App displays generation progress:
   - analyzing images
   - detecting product attributes
   - drafting Shopee listing
   - checking missing fields
   - calculating readiness score
9. App opens the Review workspace.

### Workflow 2: Review AI Draft

1. User sees a summary card:
   - detected product type
   - suggested category
   - suggested Shopee category ID/path
   - readiness score
   - readiness status
2. User sees information grouped into:
   - Detected from image
   - Provided by user
   - Inferred by AI
   - Missing information
3. User edits generated Shopee listing fields:
   - title
   - description
   - highlights
   - SEO keywords
   - hashtags
   - alt text
   - category
4. User confirms or rejects suggested attributes.
5. User fills missing required/recommended fields.
6. Readiness score updates after edits.
7. User saves product as draft or marks it ready for export.

### Workflow 3: Preview Image Selection

1. User reviews polished Shopee preview images.
2. App shows selected count and preview image metadata.
3. User selects the main image.
4. User selects supporting gallery images.
5. Selected images are included in export metadata.

Important behavior:

- Preview generation should polish the uploaded object, not invent a new product.
- Listing generation should use image analysis and user notes, not unsupported assumptions.

### Workflow 4: Export

1. User clicks Export.
2. App shows export summary:
   - total products selected
   - ready products
   - products needing review
   - missing required/recommended fields
3. If product is not Ready to Export, app warns the seller.
4. User can still export as draft JSON, but `ready_for_shopee` should be false.
5. Export includes:
   - product listing JSON
   - selected image references/assets
   - metadata per image
   - missing field warnings
   - readiness score and status
6. CSV export is not included in this phase.

---

## Page And Component Plan

### Current App Areas To Keep

- Multi-image upload.
- Background removal / product isolation.
- Shopee preview image polishing.
- Preview grid.
- Metadata JSON export.
- Progress bar.

### New Or Expanded Areas

1. **Upload And Seller Hints**
   - Add optional product note field.
   - Add required price and stock fields.
   - Add optional brand, weight, and dimensions fields.
   - Add main-image selection.

2. **Listing Draft Panel**
   - Replace generic metadata preview with structured editable listing form.
   - Fields:
     - Shopee listing title
     - category
     - description
     - product highlights
     - SEO keywords
     - hashtags
     - alt text
     - brand
     - price
     - stock
     - attributes
     - variations

3. **AI Evidence Panel**
   - Show detected/provided/inferred/missing groups.
   - Each field has source and confidence.
   - User can confirm/reject suggested attributes.

4. **Readiness Panel**
   - Score out of 100.
   - Status: Draft, Needs Review, Ready to Export, Exported.
   - Checklist grouped by importance.

5. **Export Modal**
   - Shows export summary and warnings.
   - Supports JSON export only.

---

## Readiness Scoring Plan

Use PRD weights:

| Criteria | Weight |
|---|---:|
| Product name quality | 15 |
| Product description quality | 20 |
| Product image availability | 15 |
| Attribute completeness | 20 |
| Price / stock readiness | 10 |
| Buyer trust information | 10 |
| AI confidence / user confirmation | 10 |

Initial rules:

- Product images: full points if at least one uploaded and main image selected.
- Product name: full points if title exists and user has reviewed or edited it.
- Description: full points if at least 80 characters and no unsupported claim flags.
- Attributes: partial points based on confirmed required/suggested attributes.
- Price/stock: required for Ready to Export and should receive full score only when both are provided.
- Buyer trust: score if seller provides warranty, care, material, dimensions, or relevant shipping/packaging notes.
- AI confidence: reduce score for low-confidence product type/category or unconfirmed inferred fields.

Statuses:

- `Draft`: generated but not reviewed.
- `Needs Review`: missing important details or unconfirmed inferred fields.
- `Ready to Export`: sufficient fields reviewed, confirmed category ID selected, price and stock provided, and no high-risk missing items.
- `Exported`: user exported the product.

---

## AI Output Contract

Add a backend response for listing drafts:

```json
{
  "product_profile": {
    "detected_product_type": {
      "value": "Backpack",
      "source": "detected",
      "confidence": "high",
      "needs_user_review": true
    },
    "suggested_category": {
      "value": {
        "category_id": 100636,
        "category_path": "Bags > Backpacks"
      },
      "source": "inferred",
      "confidence": "medium",
      "needs_user_review": true
    },
    "visible_attributes": [
      {
        "name": "color",
        "value": "Black",
        "source": "detected",
        "confidence": "high",
        "needs_user_review": true
      }
    ],
    "uncertain_details": ["material", "exact size", "warranty"]
  },
  "listing_draft": {
    "title": {
      "value": "20L Waterproof Laptop Backpack for School, Work & Travel - Black Multi-Compartment Bag",
      "source": "generated",
      "confidence": "medium",
      "needs_user_review": true
    },
    "description": {
      "value": "A practical everyday backpack...",
      "source": "generated",
      "confidence": "medium",
      "needs_user_review": true
    },
    "highlights": [
      {
        "value": "Laptop-friendly design",
        "source": "provided",
        "confidence": "high",
        "needs_user_review": false
      }
    ],
    "keywords": ["laptop backpack", "school bag", "office backpack"],
    "hashtags": ["#laptopbackpack", "#shopeesg"],
    "alt_text": "Black backpack with zip compartments and side pocket on a clean Shopee product preview background."
  },
  "missing_fields": [
    {
      "field": "dimensions",
      "importance": "recommended",
      "reason": "Exact dimensions are not visible from image."
    }
  ],
  "readiness": {
    "score": 78,
    "status": "Needs Review",
    "suggestions": [
      "Add exact dimensions.",
      "Add material details.",
      "Add price and stock before export."
    ]
  }
}
```

Safety rules:

- If the model is uncertain, return `missing_fields` or `uncertain_details`.
- Do not output exact material, dimensions, warranty, compatibility, certifications, official status, discounts, or urgency unless user supplied it.
- Do not mark inferred fields as confirmed.
- Preserve user-provided values if draft is regenerated.

---

## Export Contract

JSON export should include:

```json
{
  "exported_at": "2026-06-06T00:00:00.000Z",
  "platform": "Shopee",
  "target_market": "SG",
  "ready_for_shopee": false,
  "readiness": {
    "score": 78,
    "status": "Needs Review",
    "missing_required_fields": ["stock"],
    "missing_recommended_fields": ["dimensions", "material"]
  },
  "listing": {
    "product_name": "20L Waterproof Laptop Backpack for School, Work & Travel",
    "category_id": 100636,
    "category_path": "Bags > Backpacks",
    "category_confirmed": false,
    "description": "A practical everyday backpack...",
    "brand": "",
    "price": "",
    "stock": "",
    "attributes": {
      "color": "Black",
      "use_case": "School, work, travel"
    },
    "variations": []
  },
  "images": {
    "main_image": "png/backpack-main.png",
    "gallery_images": ["png/backpack-detail.png"],
    "alt_text": "Black backpack with zip compartments..."
  },
  "seo": {
    "keywords": ["laptop backpack", "school bag"],
    "hashtags": ["#laptopbackpack", "#shopeesg"]
  },
  "warnings": [
    "Final manual review in Shopee Seller Centre may still be required."
  ]
}
```

CSV export is intentionally out of scope for this phase. JSON export is the only export format for the next implementation pass.

---

## Implementation Plan For Approval

### Phase 1: Shopee Category Tree And Listing Data Model

**Files:**

- Modify: `src/shared/pipeline.js`
- Modify: `server.py`
- Modify: `tests/pipeline.test.js`
- Modify: `tests/server_py_test.py`
- Create: `data/shopee_categories.sample.json`

Tasks:

1. Add a Shopee category module that accepts flat `get_category`-style records and reconstructs:
   - category tree
   - leaf category list
   - searchable category paths
   - ID-to-path lookup
2. Add `data/shopee_categories.sample.json` with a small representative snapshot shaped like the official API response.
   - Prioritize representative records for `Electronics & Gadgets` and `Health & Beauty`.
3. Add shared listing field model with `value`, `source`, `confidence`, and `needs_user_review`.
4. Add readiness scoring utility.
5. Add missing-field detection utility.
6. Add tests for:
   - flat Shopee category records becoming display paths.
   - AI category suggestion returning an existing `category_id`, not invented text.
   - missing/unconfirmed category ID reducing readiness.
   - AI-generated fields marked reviewable.
   - price/stock not invented and required for Ready to Export.
   - missing dimensions/material/warranty flagged.
   - readiness score changes when user-provided fields are present.

### Phase 2: Backend Listing Draft Endpoint

**Files:**

- Modify: `server.py`
- Modify: `tests/server_py_test.py`

Tasks:

1. Add `POST /api/generate-listing-draft`.
2. Accept uploaded product references, seller note, category hint, Shopee category ID/path if user selected one, required price, required stock, brand, target market, and tone.
3. Return `product_profile`, `listing_draft`, `missing_fields`, `category_suggestions`, and `readiness`.
4. Use OpenAI with image inputs for product understanding if available.
5. Add fallback draft generation from existing form values when OpenAI fails.
6. Add tests for endpoint payload shape and safety behavior.

### Phase 2B: Category Sync Adapter

**Files:**

- Modify: `server.py`
- Modify: `tests/server_py_test.py`
- Create: `src/shared/categories.js` or keep category utilities inside `src/shared/pipeline.js` if staying smaller.

Tasks:

1. Add a backend category provider interface with two implementations:
   - `StaticCategoryProvider` reads `data/shopee_categories.sample.json`.
   - `ShopeeOpenPlatformCategoryProvider` later calls `GET /api/v2/product/get_category` when credentials are available.
2. Add `GET /api/categories` for the frontend category selector.
3. Return category records as:

```json
{
  "category_id": 100636,
  "parent_category_id": 100012,
  "original_category_name": "Backpacks",
  "display_path": "Bags > Backpacks",
  "has_children": false
}
```

4. Do not call unofficial Shopee web/frontend endpoints.
5. Add tests that verify the static provider never returns categories without IDs.

### Phase 3: Review UI

**Files:**

- Modify: `public/index.html`
- Modify: `public/styles.css`
- Modify: `public/app.js`

Tasks:

1. Add seller hint fields:
   - product note
   - brand
   - price
   - stock
   - weight
   - dimensions
2. Add structured editable listing panel:
   - title
   - category
   - category ID/path selector
   - description
   - highlights
   - keywords
   - hashtags
   - alt text
   - attributes
   - variations
3. Add evidence grouping:
   - detected from image
   - provided by user
   - inferred by AI
   - missing
4. Add confirm/reject behavior for AI-suggested attributes.
5. Add confirm/override behavior for AI-suggested Shopee category.
6. Add readiness score display and checklist.

### Phase 4: Export

**Files:**

- Modify: `public/app.js`
- Modify: `src/shared/zip.js` only if ZIP package needs new files.
- Modify: `tests/zip.test.js` only if ZIP format changes.

Tasks:

1. Update export JSON to use the export contract above.
2. Include selected Shopee preview images.
3. Include readiness warnings.
4. Add export summary modal/panel.

---

## Suggested First Implementation Slice

For the next coding pass, implement this narrow slice first:

1. Add listing draft model and readiness scoring tests.
2. Add `POST /api/generate-listing-draft` with deterministic fallback output.
3. Add editable listing draft panel in the current single-page app.
4. Add readiness score and missing-field checklist.
5. Update JSON export to include listing fields and warnings.

Leave Shopee API publishing, CSV export, SKU support, and catalog/dashboard features out of this pass.

---

## Settled Product Decisions

1. Price and stock are necessary seller inputs and required for `Ready to Export`.
2. SKU is not needed in this phase.
3. Product catalog/dashboard features are removed because Shopee Seller Platform already supports product catalog management.
4. Keep preview image workflow and listing review on the same page first.
5. Optimize first for `Electronics & Gadgets` and `Health & Beauty`.
6. Ignore CSV export for now; focus on JSON export.

---

## Self-Review

- Placeholder scan: no TBD/TODO placeholders.
- Scope check: feature is split into first implementation slice plus category, listing draft, review UI, and JSON export phases.
- Source alignment: chapters 8-24 of the PRD are represented; chapters 1-7 were ignored as requested.
- Safety alignment: plan explicitly separates detected, provided, inferred, missing, and confirmed data.
- Current-app alignment: plan keeps the existing preview-polishing flow and extends it with listing draft features rather than replacing it.
