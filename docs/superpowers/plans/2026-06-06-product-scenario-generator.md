# Product Scenario Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build steps 1-5 of an e-commerce AI product scenario pipeline: upload product photo and metadata, isolate product preview, generate 8-10 contextual scenes with OpenAI or local fallback, create metadata JSON, and export PNG/WebP/JSON files in a ZIP.

**Architecture:** A no-dependency Node.js server serves a static browser app and exposes one `/api/generate-scenes` endpoint. The browser owns workflow state, preview composition, WebP conversion, metadata display, and ZIP export. Shared pure JavaScript modules define geo presets, scene plans, prompt building, metadata generation, and ZIP creation so they can be tested with Node's built-in test runner.

**Tech Stack:** Node.js 18+ built-ins, browser Canvas APIs, OpenAI Images API with `gpt-image-1.5`, vanilla HTML/CSS/JS, Node `node:test`.

---

### Task 1: Shared Pipeline Logic

**Files:**
- Create: `src/shared/pipeline.js`
- Create: `tests/pipeline.test.js`
- Create: `package.json`

- [ ] Write tests for scene plan count, geo prompt details, and metadata shape.
- [ ] Run `npm test` and confirm the tests fail because files are missing.
- [ ] Implement `src/shared/pipeline.js` with geo presets, scene planning, prompt generation, metadata generation, and slug helpers.
- [ ] Run `npm test` and confirm tests pass.

### Task 2: Browser ZIP Utility

**Files:**
- Create: `src/shared/zip.js`
- Create: `tests/zip.test.js`

- [ ] Write tests that verify the ZIP output starts with the local file header and contains central directory/end records.
- [ ] Run `npm test` and confirm the ZIP tests fail because the utility is missing.
- [ ] Implement a store-only ZIP writer with CRC32, UTF-8 filenames, and Blob/Uint8Array output support.
- [ ] Run `npm test` and confirm tests pass.

### Task 3: OpenAI Server

**Files:**
- Create: `server.js`
- Create: `.gitignore`

- [ ] Implement static file serving for `public/`.
- [ ] Implement `.env` loading for `OPENAI_API_KEY`.
- [ ] Implement `/api/generate-scenes` that accepts product metadata and scene plans, calls `https://api.openai.com/v1/images/generations` with `gpt-image-1.5`, and returns base64 PNG data.
- [ ] Add graceful fallback responses when no API key is present or generation fails.

### Task 4: Seller Workflow UI

**Files:**
- Create: `public/index.html`
- Create: `public/styles.css`
- Create: `public/app.js`

- [ ] Build a first-screen usable app with upload, metadata inputs, target geo, variant count, generation mode, and pipeline status.
- [ ] Add client-side isolation preview using canvas/object-fit over a clean transparent-style stage.
- [ ] Generate scene previews from OpenAI images when available and local canvas placeholders otherwise.
- [ ] Generate metadata JSON per image and platform template guidance for Shopee, Lazada, and TikTok Shop.
- [ ] Export PNG, WebP, and metadata JSON in a ZIP.

### Task 5: Verify End-To-End

**Files:**
- Modify: `README.md`

- [ ] Document setup, `.env`, model choice, and run commands.
- [ ] Run `npm test`.
- [ ] Start the local server and verify it reports a URL.
- [ ] Report any live OpenAI call limitations clearly.
