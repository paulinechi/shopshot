# Product Requirements Document: Catalog Copilot / ShopShot

## 1. Product Overview

### Product Name
**ShopShot**  
Working concept name: **ShopShot**

### Product Type
Standalone AI web application for ecommerce sellers.

### One-liner
ShopShot turns product images into Shopee-ready product listings.

### Product Vision
Many Shopee sellers already have product photos but do not have structured product information, optimized titles, detailed descriptions, attributes, keywords, or upload-ready listing content. ShopShot starts from product images and uses AI to generate editable product catalog entries that can be reviewed and exported for Shopee.

The MVP will focus only on Shopee. Other ecommerce channels such as Lazada, TikTok Shop, Shopify, Amazon-style listings, Instagram, and Google Shopping will be treated as future roadmap items.

### MVP Tagline
**Upload images. Generate Shopee listings. Sell faster.**

---

## 2. Problem Statement

Shopee sellers often need to create product listings manually from product photos, supplier notes, spreadsheets, or existing informal product information. This process is repetitive, time-consuming, and error-prone.

The main pain points are:

1. **Product images exist, but structured listing data is missing**  
   Sellers may have photos of the product, but not a clean product name, category, description, product attributes, keywords, SKU, or variation structure.

2. **Manual Shopee listing creation takes time**  
   Sellers need to fill in product names, descriptions, prices, stock, categories, product images, variations, and attributes.

3. **Shopee listings need completeness and clarity**  
   Missing details such as size, material, color, dimensions, warranty, or compatibility can reduce buyer trust and make listings harder to review.

4. **AI can help, but needs seller confirmation**  
   Product images alone may not confirm exact material, dimensions, certification, warranty, or compatibility. The system must clearly separate detected, inferred, and missing information.

5. **Bulk preparation is still painful**  
   Even if Shopee supports product upload and mass update workflows, sellers still need to prepare clean and complete product data before upload.

---

## 3. Product Positioning

ShopShot is an **AI-first Shopee listing creation tool**.

It is not just a product description generator. It helps sellers:

1. Upload product images.
2. Generate a draft Shopee product listing using AI.
3. Review and confirm AI-detected product information.
4. Improve product title, description, attributes, and keywords.
5. Check missing listing information before export.
6. Export Shopee-ready product data.

### Positioning Statement

**ShopShot helps Shopee sellers create product listings from images and prepare them for upload faster.**

---

## 4. Target Users

### Primary User: Small Shopee Seller
A seller who has product photos but does not have structured Shopee listing content. They want to create listings quickly without writing everything manually.

### Secondary User: Growing Shopee Store Owner
A seller managing multiple SKUs who wants to standardize titles, descriptions, attributes, and listing quality.

### Tertiary User: Ecommerce Operations Team
A team preparing many products for Shopee and needing to review, enrich, and export listing data efficiently.

---

## 5. Goals and Objectives

### Business Goals

1. Reduce the time required to create Shopee listings.
2. Help sellers convert product images into structured Shopee listing data.
3. Improve listing completeness, clarity, and buyer trust.
4. Support a simple review-before-export workflow.
5. Build a foundation for future Shopee API integration or mass upload automation.

### User Goals

1. Create Shopee product listings from images with minimal manual input.
2. Avoid writing product names and descriptions from scratch.
3. Identify missing product information before publishing.
4. Generate Shopee-style titles, descriptions, attributes, and keywords.
5. Export Shopee-ready listing data for manual upload or future direct publishing.

---

## 6. MVP Scope

### MVP Scope

The MVP will focus on **image-to-Shopee listing generation**.

Users can:

1. Upload one or more product images.
2. Optionally add a short product note.
3. Let AI generate a draft Shopee product profile.
4. Review detected, inferred, and missing information.
5. Edit or confirm AI-generated fields.
6. Generate a Shopee-style product title and description.
7. Generate suggested Shopee attributes and keywords.
8. View a Shopee readiness score.
9. Save products into a simple catalog dashboard.
10. Export product data as CSV, JSON, or Shopee-style upload file.

### Out of Scope for MVP

The following features are not included in the MVP:

1. Direct publishing to Shopee via API.
2. Live Shopee Seller Centre account connection.
3. Lazada, TikTok Shop, Shopify, Amazon, Instagram, or Google Shopping output.
4. Full user account and billing system.
5. Inventory and order management.
6. Pricing automation.
7. Competitor scraping.
8. AI image generation or image editing.
9. Full official Shopee template compliance for every product category.
10. Multi-country Shopee compliance engine.

---

## 7. Core Product Concept

The starting point of the product is product images.

### Core Flow

```text
Upload product images
↓
AI analyzes the product
↓
AI generates a draft Shopee listing
↓
User reviews and edits
↓
System checks missing Shopee listing information
↓
User exports Shopee-ready content
```

---

## 8. Shopee MVP Listing Fields

The MVP should generate or support the following Shopee-style fields:

| Field | Source | Notes |
|---|---|---|
| Product Name | AI-generated + user editable | Shopee-style, keyword-friendly title |
| Product Category | AI-suggested + user editable | Based on image and product note |
| Product Description | AI-generated + user editable | Buyer-friendly product description |
| Product Images | User-uploaded | Main image plus supporting images |
| Product Attributes | AI-suggested + user confirmation | Color, material, size, use case, etc. |
| Price | User input | Optional in MVP but recommended |
| Stock | User input | Optional in MVP but recommended |
| SKU | User input or auto-generated | Optional in MVP |
| Variations | AI-suggested + user editable | Example: color, size, bundle |
| Weight / Dimensions | User input | Flag as missing if not provided |
| Missing Fields | System-generated | Used for readiness check |

---

## 9. User Journey

### Main User Flow: Image-to-Shopee Listing

1. User lands on ShopShot homepage.
2. User clicks “Create Shopee Listing.”
3. User uploads one or more product images.
4. User optionally adds a short product note, such as “waterproof laptop backpack, 20L.”
5. AI analyzes the uploaded images.
6. AI generates a draft Shopee listing.
7. System displays:
   - detected product type
   - suggested Shopee product name
   - suggested category
   - detected visual attributes
   - suggested product description
   - suggested product highlights
   - suggested attributes
   - missing information checklist
8. User reviews and edits the draft.
9. User confirms or rejects AI-suggested fields.
10. System calculates Shopee readiness score.
11. User saves the product into the catalog.
12. User exports the product as CSV, JSON, or Shopee-style upload file.

---

## 10. User Input Requirements

### Required Inputs

| Field | Type | Description |
|---|---|---|
| Product Images | Image upload | One or more product images uploaded by user |

### Optional Inputs

| Field | Type | Description |
|---|---|---|
| Product Note | Text input | Rough product hint, e.g. “20L waterproof backpack” |
| Product Category Hint | Dropdown / text | Optional seller-provided category |
| Price | Number | Product price |
| Stock | Number | Available stock |
| SKU | Text | Seller SKU |
| Brand | Text | Product brand, if applicable |
| Variation Details | Text / form | Color, size, bundle, etc. |
| Target Market | Dropdown | Default: Singapore |
| Tone | Dropdown | Default: clear and buyer-friendly |

---

## 11. Functional Requirements

### FR1: Product Image Upload

**Description**  
Users must be able to upload product images as the starting point for Shopee listing creation.

**Acceptance Criteria**

- User can upload one or more PNG or JPG images.
- User can preview uploaded images before generation.
- User can remove or replace uploaded images.
- User can select a main product image.
- System shows a clear error if the file type or size is not supported.

---

### FR2: Multi-image Product Understanding

**Description**  
The system should analyze multiple product images to improve listing quality.

**Acceptance Criteria**

- System uses all uploaded images to identify product type and visible features.
- System identifies front, side, detail, packaging, or lifestyle images where possible.
- System detects visible color, style, shape, and product components.
- System flags uncertainty if uploaded images appear inconsistent or unrelated.
- System can suggest variants if images show different colors or styles.

---

### FR3: AI-generated Shopee Listing Draft

**Description**  
The system should generate a draft Shopee listing from uploaded images and optional notes.

**Acceptance Criteria**

- System generates:
  - Shopee-style product name
  - product type
  - suggested Shopee category
  - short product description
  - product highlights
  - keywords
  - visible attributes
  - suggested attributes
  - missing information checklist
- System separates information into:
  - detected from image
  - provided by user
  - inferred by AI
  - missing and needs confirmation
- User can edit all generated fields before saving or exporting.

---

### FR4: Product Review and Confirmation

**Description**  
Users must be able to review and confirm AI-generated Shopee listing data.

**Acceptance Criteria**

- User can edit product name, category, description, highlights, attributes, price, stock, and SKU.
- User can accept or reject AI-suggested attributes.
- User can manually add missing product information.
- User can regenerate the listing draft.
- User can save the product as draft.
- User can mark the product as ready for export.

---

### FR5: Shopee Readiness Score

**Description**  
The system should provide a readiness score from 0 to 100 for each Shopee listing.

**Acceptance Criteria**

- Score is displayed after draft generation.
- Score updates after user edits product information.
- Score is based on:
  - completeness
  - title quality
  - description quality
  - image availability
  - attribute completeness
  - price / stock availability
  - AI confidence and user confirmation
- System provides practical improvement suggestions.

### Suggested Scoring Logic

| Criteria | Weight |
|---|---:|
| Product name quality | 15 |
| Product description quality | 20 |
| Product image availability | 15 |
| Attribute completeness | 20 |
| Price / stock / SKU readiness | 10 |
| Buyer trust information | 10 |
| AI confidence / user confirmation | 10 |
| Total | 100 |

### Readiness Statuses

| Status | Meaning |
|---|---|
| Draft | Product has been generated but not reviewed |
| Needs Review | Important details are missing or uncertain |
| Ready to Export | Product is complete enough for export |
| Exported | Product has been exported before |

---

### FR6: Missing Attribute Detection

**Description**  
The system should identify missing or uncertain product details before Shopee export.

**Acceptance Criteria**

- System checks for missing:
  - category
  - product name
  - description
  - images
  - price
  - stock
  - SKU
  - color
  - material
  - size
  - weight
  - dimensions
  - warranty
  - compatibility
  - variation details
- Missing fields should be grouped by importance.
- User can add missing details and regenerate listing content.
- System updates readiness score after missing details are added.

---

### FR7: Product Catalog Dashboard

**Description**  
Users should be able to view and manage products created through image upload.

**Acceptance Criteria**

- User can view products in a catalog table.
- Each product row should show:
  - product image
  - product name
  - suggested category
  - SKU, if available
  - price, if available
  - readiness status
  - readiness score
- User can search products by name or SKU.
- User can filter by readiness status.
- User can select products for export.
- User can open a product detail page.

---

### FR8: Product Detail Page

**Description**  
Users should be able to view and edit full product listing details.

**Acceptance Criteria**

- User can view all uploaded images.
- User can edit product name, category, description, price, stock, SKU, and attributes.
- User can manage variants such as color, size, or bundle.
- User can view AI suggestions and missing fields.
- User can regenerate listing content.
- User can save changes.

---

### FR9: Shopee-style Export

**Description**  
Users should be able to export selected products into a Shopee-style upload structure.

**Acceptance Criteria**

- User can export one or more selected products.
- Export includes:
  - product name
  - product description
  - category
  - brand
  - price
  - stock
  - SKU
  - variations
  - attributes
  - image references
  - weight and dimensions, if available
  - missing field warnings
- User can download export as CSV or JSON.
- System generates an export summary:
  - total products selected
  - products ready
  - products needing review
  - products missing required fields
- System warns that final manual review in Shopee Seller Centre may still be required.

---

## 12. AI Behavior Requirements

### AI Should

1. Identify likely product type from uploaded images.
2. Detect visible attributes such as color, shape, style, visible components, and packaging.
3. Generate Shopee-style product names that are clear and keyword-friendly.
4. Generate buyer-friendly product descriptions.
5. Suggest relevant product attributes.
6. Suggest missing information.
7. Separate detected facts from assumptions.
8. Flag uncertainty clearly.
9. Preserve user-confirmed product information.
10. Avoid unsupported claims.

### AI Should Not

1. Invent exact specifications not visible or provided.
2. Claim specific material, size, warranty, compatibility, certification, or safety information unless provided.
3. Make medical, health, legal, or regulated product claims without evidence.
4. Claim a product is “official,” “certified,” “guaranteed,” or “best-selling” unless provided.
5. Generate fake discounts or fake urgency.
6. Export without user review.
7. Treat AI-inferred information as confirmed fact.

---

## 13. Example Output

### Input

**Images:** 3 product images of a black backpack  
**Optional note:** “Waterproof laptop backpack, 20L, for students and office workers”  
**Target platform:** Shopee  
**Tone:** Clear and buyer-friendly

### AI-generated Shopee Product Profile

**Detected Product Type**  
Backpack

**Suggested Category**  
Bags > Backpacks

**Detected Visual Attributes**  
- Black color
- Zip compartments
- Shoulder straps
- Side pocket
- Minimal design

**Provided by User**  
- Waterproof
- Laptop backpack
- 20L capacity
- For students and office workers

**Suggested Product Name**  
20L Waterproof Laptop Backpack for School, Work & Travel – Black Multi-Compartment Bag

**Product Description**  
A practical everyday backpack for students, office workers, and commuters. This 20L waterproof laptop backpack is designed to keep your daily essentials organized for school, work, and short trips.

**Product Highlights**

- 20L capacity
- Laptop-friendly design
- Waterproof feature based on seller input
- Suitable for school, office, commuting, and travel
- Clean black design

**Suggested Keywords**  
waterproof backpack, laptop backpack, school bag, office backpack, travel backpack, black backpack

**Missing Information**

- Exact dimensions
- Material
- Laptop size compatibility
- Weight
- Warranty
- Care instructions

**Shopee Readiness Score**  
78/100

**Suggested Improvements**

1. Add exact dimensions.
2. Add material details.
3. Specify compatible laptop size.
4. Add warranty or care instructions.
5. Add price and stock before export.

---

## 14. Information Architecture

### Main Pages

1. **Landing Page**
   - Product value proposition
   - “Create Shopee Listing” CTA
   - Before/after example
   - Demo of image-to-listing generation

2. **Create Shopee Listing Page**
   - Image upload
   - Optional product note
   - Optional price, stock, SKU
   - Generate button

3. **AI Draft Review Page**
   - Uploaded images
   - AI-generated Shopee listing
   - Detected vs inferred vs missing information
   - Edit and confirm actions
   - Shopee readiness score

4. **Catalog Dashboard**
   - Product table
   - Readiness status
   - Search and filters
   - Bulk select
   - Export action

5. **Product Detail Page**
   - Full product record
   - Images
   - Attributes
   - AI suggestions
   - Edit and save actions

6. **Export Modal / Export Page**
   - Preview export fields
   - Export summary
   - Download CSV / JSON

---

## 15. MVP Wireframe Structure

### Create Shopee Listing Page

```text
------------------------------------------------
ShopShot
------------------------------------------------

Create Shopee Listing with AI

Upload Product Images
[ Drag and drop product images here ]

Optional Product Note
[ e.g. waterproof laptop backpack, 20L, for students ]

Optional Listing Details
Price: [        ]
Stock: [        ]
SKU:   [        ]

[ Generate Shopee Listing ]
------------------------------------------------
```

### AI Draft Review Page

```text
------------------------------------------------
AI-generated Shopee Listing
------------------------------------------------

Uploaded Images
[ Image 1 ] [ Image 2 ] [ Image 3 ]

Detected Product Type: Backpack
Suggested Category: Bags > Backpacks
Detected Color: Black

Detected from Image
- Zip compartments
- Shoulder straps
- Side pocket

Provided by User
- Waterproof
- 20L
- Laptop backpack

Missing Information
- Dimensions
- Material
- Laptop size compatibility
- Warranty

Shopee Readiness Score: 78/100

Product Name
[ 20L Waterproof Laptop Backpack for School, Work & Travel ]

Product Description
[ Editable text box ]

Product Highlights
[ Editable bullet list ]

[ Save Draft ] [ Regenerate ] [ Mark Ready ] [ Export ]
------------------------------------------------
```

---

## 16. Technical Architecture

### Frontend

Recommended options:

- React
- Next.js
- Tailwind CSS

### Backend

Recommended options:

- Node.js / Express
- Python / FastAPI

### AI Layer

The AI layer should include:

1. Vision model for product image understanding.
2. LLM for Shopee listing generation.
3. Rules engine for readiness scoring and missing attribute detection.
4. Export mapping logic for Shopee-style output.

### Data Flow

```text
Product Images
↓
Image Understanding Layer
↓
Structured Product Profile
↓
Shopee Listing Generation
↓
User Review and Confirmation
↓
Product Catalog Database
↓
Readiness Scoring Engine
↓
Shopee-style Export Engine
```

---

## 17. Prompting Logic

### Step 1: Image Understanding Prompt

The AI should analyze uploaded product images and return a structured product profile.

Expected output:

```json
{
  "detected_product_type": "Backpack",
  "detected_color": "Black",
  "visible_features": ["zip compartments", "shoulder straps", "side pocket"],
  "possible_category": "Bags > Backpacks",
  "image_confidence": {
    "product_type": "high",
    "color": "high",
    "material": "low"
  },
  "uncertain_details": ["material", "exact size", "waterproof capability"]
}
```

### Step 2: Shopee Listing Draft Prompt

The AI should generate an editable Shopee listing draft based on image analysis and user notes.

Expected output:

```json
{
  "suggested_product_name": "20L Waterproof Laptop Backpack for School, Work & Travel – Black Multi-Compartment Bag",
  "suggested_category": "Bags > Backpacks",
  "product_description": "A practical everyday backpack for students, office workers, and commuters...",
  "product_highlights": [
    "20L capacity",
    "Laptop-friendly design",
    "Suitable for school, office, commuting, and travel"
  ],
  "suggested_attributes": {
    "color": "Black",
    "use_case": "School, work, travel"
  },
  "missing_fields": [
    "dimensions",
    "material",
    "laptop size compatibility",
    "warranty",
    "price",
    "stock"
  ]
}
```

### Step 3: Readiness Scoring Prompt

The AI and rules engine should assess:

- Is the product name clear and searchable?
- Is the product description complete?
- Are images available?
- Are price, stock, and SKU available?
- Are key attributes missing?
- Are uncertain claims clearly flagged?
- Is the product ready for Shopee export?

---

## 18. Non-Functional Requirements

### Performance

- Image upload preview should be fast and responsive.
- AI draft generation should complete within an acceptable time for demo usage.
- System should show loading status while AI is processing images.

### Reliability

- System should handle incomplete or unclear images gracefully.
- System should allow users to manually correct AI output.
- System should avoid exporting unsupported or unreviewed claims as confirmed facts.

### Usability

- Interface should be simple enough for non-technical sellers.
- Main image-to-Shopee flow should be completed in under 3 minutes.
- Detected, inferred, and missing information should be visually separated.
- Generated content should be easy to edit and export.

### Security and Privacy

- Uploaded product images should only be used for product generation and catalog management.
- User data should not be exposed to other users.
- If data is stored, the system should clearly communicate what is saved.

---

## 19. Success Metrics

### MVP Success Metrics

1. User can create a draft Shopee listing from images in under 3 minutes.
2. System can generate product name, description, category, attributes, and keywords from product images.
3. System clearly separates detected, inferred, and missing information.
4. User can review and edit the AI-generated draft.
5. User can view a Shopee readiness score.
6. User can export selected product listings.
7. Demo users understand the value within 30 seconds.

### Product Success Metrics

1. Average time saved per Shopee listing.
2. Number of products created from images.
3. Percentage of AI-generated drafts saved by users.
4. Percentage of products reaching “Ready to Export” status.
5. Percentage of users exporting generated content.
6. Improvement in readiness score after user review.
7. User satisfaction rating for generated listing quality.

---

## 20. Risks and Mitigations

### Risk 1: AI invents unsupported product details

**Mitigation**  
Separate detected, provided, inferred, and missing information. Require user confirmation for uncertain fields.

### Risk 2: Product image is unclear or incomplete

**Mitigation**  
Ask the user to upload more images or add a short product note.

### Risk 3: Output may not match exact Shopee category requirements

**Mitigation**  
For MVP, generate Shopee-style output and flag final manual review. Add official category/template mapping in future phases.

### Risk 4: Seller exports inaccurate product information

**Mitigation**  
Show readiness warnings and require user review before export.

### Risk 5: Too many features for hackathon

**Mitigation**  
Focus on one clear flow: upload images → generate Shopee listing → review → export.

---

## 21. MVP Build Plan

### Day 1: Image-to-Shopee Creation Flow

- Build landing page.
- Build image upload interface.
- Add optional product note input.
- Add optional price, stock, and SKU fields.
- Implement uploaded image preview.

### Day 2: AI Shopee Listing Generation

- Implement image understanding prompt.
- Generate structured product profile.
- Generate Shopee product name, description, highlights, keywords, and missing fields.
- Build AI draft review page.

### Day 3: Catalog, Readiness Score, and Export

- Build product catalog dashboard.
- Add Shopee readiness score.
- Add missing attribute checker.
- Add copy and export functions.
- Polish demo flow.

---

## 22. Future Roadmap

### Phase 2: Bulk Image Upload

- User uploads a folder of product images.
- System groups images by product.
- AI creates multiple draft Shopee listings.
- User reviews products in a catalog table.

### Phase 3: Shopee Template Export

- Improve export compatibility with Shopee mass upload templates.
- Add category-specific field mapping.
- Support variations and image packaging more accurately.

### Phase 4: Shopee API Integration

- Connect seller account through Shopee Open Platform.
- Upload product images to Shopee media space.
- Create or update Shopee product listings after user review.

### Phase 5: CSV and Excel Import

- User uploads existing catalog files.
- System maps fields automatically.
- AI enriches existing product data.
- User exports Shopee-ready files.

### Phase 6: Localization

- Support different Shopee markets and languages.
- Adapt listing copy and attributes by market.

### Phase 7: Multi-channel Expansion

- Add Lazada, TikTok Shop, Shopify, Instagram, Amazon-style listings, and Google Shopping.

---

## 23. Open Questions

1. Should the MVP support one product at a time or multiple products at once?
2. Should export be generic CSV, JSON, or Shopee-style Excel template?
3. Should price, stock, and SKU be required before export?
4. Which product categories should be tested first?
5. Should the system save products permanently or only for the hackathon demo?
6. Should the product name follow a specific Shopee title formula?
7. Should we include a category picker or rely on AI category suggestion for MVP?

---

## 24. Recommended Hackathon Positioning

ShopShot is an AI-first Shopee listing builder. It helps sellers transform product images into structured, editable, and export-ready Shopee listings.

The strongest demo message is:

**“Upload product images. Generate Shopee listings. Export in minutes.”**

### Demo Story

**Before:**  
A seller has product photos but no structured Shopee listing content. Creating product names, descriptions, attributes, keywords, and upload-ready files manually takes time.

**After:**  
The seller uploads product images into ShopShot. AI identifies the product, generates a draft Shopee listing, flags missing details, calculates readiness, and exports marketplace-ready content.

### Core Hackathon Demo Flow

```text
Upload product images
→ AI generates Shopee product profile
→ User reviews detected and missing information
→ AI creates Shopee listing
→ User exports Shopee-ready content
```
