# Shopee Product Preview Polisher

End-to-end hackathon slice for steps 1-5 of the contextual e-commerce product scenario pipeline.

## What It Builds

1. Seller uploads one or more product photos and metadata.
2. The browser asks the Python backend to isolate each product reference with a transparent background.
3. The app polishes the uploaded object into 8-10 Shopee product-preview variations and updates progress as each variant finishes.
4. The app creates metadata JSON per image with SEO tags, alt text, Shopee copy, and TikTok hashtags.
5. The seller exports a ZIP with PNG, WebP, and metadata JSON files.

## OpenAI Image Generation

The Python backend reads `OPENAI_API_KEY` from `.env` and calls the OpenAI Images API with:

```text
OPENAI_IMAGE_MODEL=gpt-image-1.5
```

`gpt-image-1.5` is the latest OpenAI image model in the current official docs. If uploaded product references are present, the backend uses image edits so the object stays based on the original photo instead of being invented from text. If a live API call fails or the key is missing, the app falls back to local canvas-composited previews so the workflow remains demoable. Background removal uses the OpenAI image edits endpoint with transparent-background output; a local `rembg` integration is the next no-cost/offline fallback candidate.

## Run

```bash
npm test
npm start
```

Open:

```text
http://localhost:3000
```

## .env

```text
OPENAI_API_KEY=your_key_here
OPENAI_IMAGE_MODEL=gpt-image-1.5
```

`OPENAI_IMAGE_MODEL` is optional. The default is `gpt-image-1.5`.

## Notes

- No package install is required; the app uses Python, Node.js test tooling, and browser built-ins.
- Local scene export creates 1200x1200 PNG assets and browser-optimized WebP variants.
- OpenAI product preview generation uses uploaded product references and preservation prompts. It should polish lighting, background, and listing presentation while keeping the original object shape, label, packaging, color, and branding intact.
