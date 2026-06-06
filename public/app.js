import {
  buildGenerationPayload,
  buildScenePlans,
  generateImageMetadata,
  slugify
} from "../src/shared/pipeline.js";
import { createZipBlob } from "../src/shared/zip.js";

const state = {
  productImages: [],
  isolatedImages: [],
  scenes: [],
  metadata: []
};

const els = {
  apiStatus: document.querySelector("#apiStatus"),
  productImage: document.querySelector("#productImage"),
  uploadStrip: document.querySelector("#uploadStrip"),
  isolationCanvas: document.querySelector("#isolationCanvas"),
  generateButton: document.querySelector("#generateButton"),
  exportButton: document.querySelector("#exportButton"),
  pipelineStatus: document.querySelector("#pipelineStatus"),
  progressBar: document.querySelector("#progressBar"),
  progressLabel: document.querySelector("#progressLabel"),
  sceneGrid: document.querySelector("#sceneGrid"),
  metadataPreview: document.querySelector("#metadataPreview"),
  resultSummary: document.querySelector("#resultSummary")
};

const fields = ["productName", "category", "brandTone", "audience", "targetGeo", "count"]
  .reduce((items, id) => ({ ...items, [id]: document.querySelector(`#${id}`) }), {});

const PIPELINE_STEPS = [
  "Seller photo and metadata captured",
  "Product isolated into clean preview",
  "Scene variants generated",
  "Metadata JSON generated",
  "PNG, WebP, and metadata ZIP ready"
];

init();

async function init() {
  renderPipelineStatus(0);
  drawIsolationPlaceholder();
  await refreshApiStatus();
  els.productImage.addEventListener("change", handleImageUpload);
  els.generateButton.addEventListener("click", generateScenes);
  els.exportButton.addEventListener("click", exportZip);
}

async function refreshApiStatus() {
  try {
    const response = await fetch("/api/health");
    const health = await response.json();
    els.apiStatus.textContent = health.openaiConfigured ? `OpenAI ${health.imageModel}` : "Local fallback";
    els.apiStatus.classList.toggle("warn", !health.openaiConfigured);
  } catch {
    els.apiStatus.textContent = "Offline fallback";
    els.apiStatus.classList.add("warn");
  }
}

async function handleImageUpload(event) {
  const files = [...event.target.files].filter((file) => file.type.startsWith("image/"));
  if (!files.length) return;

  revokeProductUrls();
  state.productImages = files.map((file, index) => ({
    id: `product-${index + 1}`,
    file,
    name: file.name,
    sourceUrl: URL.createObjectURL(file),
    isolatedUrl: "",
    isolatedBlob: null,
    status: "uploaded"
  }));
  state.isolatedImages = [];
  renderUploadStrip();
  drawIsolationPreview();
  setProgress(0, state.productImages.length, "Removing backgrounds...");

  await removeBackgrounds();
  renderUploadStrip();
  drawIsolationPreview();
  renderPipelineStatus(2);
}

async function generateScenes() {
  els.generateButton.disabled = true;
  els.exportButton.disabled = true;
  els.generateButton.textContent = "Generating...";
  renderPipelineStatus(state.productImages.length ? 2 : 1);

  const input = getInput();
  const localPayload = buildGenerationPayload(input);
  const productImages = await getProductReferencePayloads();
  state.metadata = localPayload.metadata;
  state.scenes = [];
  renderScenes();
  setProgress(0, localPayload.plans.length, `Generating 0 of ${localPayload.plans.length} variants`);

  for (let index = 0; index < localPayload.plans.length; index += 1) {
    const plan = localPayload.plans[index];
    const metadata = localPayload.metadata[index];
    let payload = {
      mode: "fallback",
      plan,
      metadata,
      image: null
    };

    if (getMode() === "openai") {
      try {
        const response = await fetch("/api/generate-scene", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...input, planId: plan.id, index, productImages })
        });
        payload = await response.json();
      } catch (error) {
        payload.image = { id: plan.id, source: "fallback", error: error.message };
      }
    }

    const [scene] = await buildSceneOutputs({
      mode: payload.mode,
      plans: [payload.plan || plan],
      metadata: [payload.metadata || metadata],
      images: payload.image ? [payload.image] : []
    }, input);
    state.scenes.push(scene);
    renderScenes();
    setProgress(index + 1, localPayload.plans.length, `Generated ${index + 1} of ${localPayload.plans.length} variants`);
  }

  renderMetadata();
  renderPipelineStatus(5);
  els.resultSummary.textContent = `${state.scenes.length} scenes ready`;
  els.exportButton.disabled = false;
  els.generateButton.disabled = false;
  els.generateButton.textContent = "Generate scenes";
}

async function buildSceneOutputs(payload, input) {
  const outputs = [];
  for (const plan of payload.plans) {
    const metadata = payload.metadata.find((item) => item.id === plan.id) || generateImageMetadata(plan, input);
    const openAiImage = payload.images?.find((image) => image.id === plan.id && image.b64);

    if (openAiImage) {
      const dataUrl = `data:${openAiImage.mimeType || "image/png"};base64,${openAiImage.b64}`;
      outputs.push({
        id: plan.id,
        plan,
        metadata,
        source: "OpenAI",
        imageUrl: dataUrl,
        pngBlob: await dataUrlToBlob(dataUrl)
      });
    } else {
      const fallback = await createLocalScene(plan, metadata);
      outputs.push({
        id: plan.id,
        plan,
        metadata,
        source: payload.mode === "openai" ? "Fallback" : "Local",
        ...fallback
      });
    }
  }
  return outputs;
}

async function removeBackgrounds() {
  if (!state.productImages.length) return;

  try {
    const images = await Promise.all(state.productImages.map(async (item) => ({
      name: item.name,
      mimeType: item.file.type,
      b64: await fileToBase64(item.file)
    })));

    const response = await fetch("/api/remove-background", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ images })
    });
    const payload = await response.json();

    state.productImages = await Promise.all(state.productImages.map(async (item, index) => {
      const output = payload.images?.[index];
      if (output?.b64) {
        const dataUrl = `data:${output.mimeType || "image/png"};base64,${output.b64}`;
        return {
          ...item,
          isolatedUrl: dataUrl,
          isolatedBlob: await dataUrlToBlob(dataUrl),
          status: "isolated"
        };
      }
      return {
        ...item,
        isolatedUrl: item.sourceUrl,
        isolatedBlob: item.file,
        status: output?.error ? "fallback" : "uploaded"
      };
    }));
  } catch {
    state.productImages = state.productImages.map((item) => ({
      ...item,
      isolatedUrl: item.sourceUrl,
      isolatedBlob: item.file,
      status: "fallback"
    }));
  }

  state.isolatedImages = state.productImages.filter((item) => item.isolatedUrl);
  setProgress(state.productImages.length, state.productImages.length, "Background removal complete");
}

function renderUploadStrip() {
  els.uploadStrip.innerHTML = "";
  for (const item of state.productImages) {
    const thumb = document.createElement("div");
    thumb.className = "upload-thumb";
    const image = document.createElement("img");
    image.src = item.isolatedUrl || item.sourceUrl;
    image.alt = item.name;
    const label = document.createElement("span");
    label.textContent = item.status === "isolated" ? "isolated" : item.status;
    thumb.append(image, label);
    els.uploadStrip.append(thumb);
  }
}

function renderScenes() {
  els.sceneGrid.innerHTML = "";

  for (const scene of state.scenes) {
    const card = document.createElement("article");
    card.className = "scene-card";

    const image = document.createElement("img");
    image.src = scene.imageUrl;
    image.alt = scene.metadata.altText;

    const body = document.createElement("div");
    body.className = "scene-card-body";
    body.innerHTML = `
      <h3>${escapeHtml(scene.plan.sceneType)}</h3>
      <p>${escapeHtml(scene.plan.geo.market)} · ${escapeHtml(scene.plan.category)}</p>
      <span class="source-badge ${scene.source === "Fallback" ? "warn" : ""}">${escapeHtml(scene.source)}</span>
    `;

    card.append(image, body);
    els.sceneGrid.append(card);
  }
}

function renderMetadata() {
  els.metadataPreview.textContent = JSON.stringify({
    generatedAt: new Date().toISOString(),
    imageCount: state.metadata.length,
    images: state.metadata
  }, null, 2);
}

async function exportZip() {
  if (!state.scenes.length) return;
  els.exportButton.disabled = true;
  els.exportButton.textContent = "Bundling...";

  const files = [
    {
      name: "metadata.json",
      data: JSON.stringify({
        generatedAt: new Date().toISOString(),
        images: state.metadata
      }, null, 2)
    }
  ];

  for (const scene of state.scenes) {
    const baseName = scene.metadata.fileBaseName;
    files.push({
      name: `png/${baseName}.png`,
      data: new Uint8Array(await scene.pngBlob.arrayBuffer())
    });

    const webp = await imageUrlToWebp(scene.imageUrl);
    files.push({
      name: `webp/${baseName}.webp`,
      data: new Uint8Array(await webp.arrayBuffer())
    });

    files.push({
      name: `metadata/${baseName}.json`,
      data: JSON.stringify(scene.metadata, null, 2)
    });
  }

  const zip = createZipBlob(files);
  const url = URL.createObjectURL(zip);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${slugify(fields.productName.value || "product")}-scenario-export.zip`;
  link.click();
  URL.revokeObjectURL(url);

  els.exportButton.disabled = false;
  els.exportButton.textContent = "Export ZIP";
}

function getInput() {
  return {
    productName: fields.productName.value,
    category: fields.category.value,
    brandTone: fields.brandTone.value,
    audience: fields.audience.value,
    targetGeo: fields.targetGeo.value,
    count: Number(fields.count.value) || 8
  };
}

function getMode() {
  return document.querySelector("input[name='mode']:checked")?.value || "openai";
}

async function getProductReferencePayloads() {
  const references = state.productImages.slice(0, 4);
  return Promise.all(references.map(async (item) => {
    const blob = item.isolatedBlob || item.file;
    return {
      name: item.name,
      mimeType: blob.type || item.file.type || "image/png",
      b64: await blobToBase64(blob)
    };
  }));
}

function renderPipelineStatus(doneCount) {
  els.pipelineStatus.innerHTML = PIPELINE_STEPS.map((label, index) => `
    <li class="${index < doneCount ? "done" : ""}">
      <b>${index + 1}</b>
      <span>${label}</span>
    </li>
  `).join("");
}

function setProgress(done, total, label) {
  const percent = total ? Math.round((done / total) * 100) : 0;
  els.progressBar.style.width = `${percent}%`;
  els.progressLabel.textContent = label;
}

function revokeProductUrls() {
  for (const item of state.productImages) {
    URL.revokeObjectURL(item.sourceUrl);
    if (item.isolatedUrl?.startsWith("blob:")) URL.revokeObjectURL(item.isolatedUrl);
  }
}

function drawIsolationPlaceholder() {
  const canvas = els.isolationCanvas;
  const context = canvas.getContext("2d");
  context.clearRect(0, 0, canvas.width, canvas.height);
  drawChecker(context, canvas.width, canvas.height);
  context.fillStyle = "#2f7d5a";
  context.font = "700 30px system-ui";
  context.textAlign = "center";
  context.fillText("Upload a product photo", canvas.width / 2, canvas.height / 2 - 6);
  context.fillStyle = "#667064";
  context.font = "18px system-ui";
  context.fillText("The isolated product preview appears here", canvas.width / 2, canvas.height / 2 + 28);
}

async function drawIsolationPreview() {
  const canvas = els.isolationCanvas;
  const context = canvas.getContext("2d");
  context.clearRect(0, 0, canvas.width, canvas.height);
  drawChecker(context, canvas.width, canvas.height);

  const images = state.productImages.slice(0, 4);
  if (!images.length) {
    drawIsolationPlaceholder();
    return;
  }

  const columns = Math.min(2, images.length);
  const rows = Math.ceil(images.length / columns);
  const cellWidth = canvas.width / columns;
  const cellHeight = (canvas.height - 90) / rows;

  for (let index = 0; index < images.length; index += 1) {
    const image = await loadImage(images[index].isolatedUrl || images[index].sourceUrl);
    const column = index % columns;
    const row = Math.floor(index / columns);
    drawContainedImage(context, image, column * cellWidth + 24, row * cellHeight + 20, cellWidth - 48, cellHeight - 36);
  }

  context.fillStyle = "rgba(255, 255, 255, 0.86)";
  roundRect(context, 24, canvas.height - 78, 390, 46, 8);
  context.fill();
  context.fillStyle = "#185a3d";
  context.font = "700 18px system-ui";
  context.textAlign = "left";
  context.fillText(`${images.length} product reference${images.length === 1 ? "" : "s"} isolated`, 42, canvas.height - 48);
}

async function createLocalScene(plan, metadata) {
  const canvas = document.createElement("canvas");
  canvas.width = 1200;
  canvas.height = 1200;
  const context = canvas.getContext("2d");
  drawSceneBackground(context, plan);

  const productReference = state.isolatedImages[plan.index % Math.max(state.isolatedImages.length, 1)]
    || state.productImages[plan.index % Math.max(state.productImages.length, 1)];

  if (productReference?.isolatedUrl || productReference?.sourceUrl) {
    const image = await loadImage(productReference.isolatedUrl || productReference.sourceUrl);
    drawProductHero(context, image);
  } else {
    drawProductPlaceholder(context, metadata);
  }

  drawSceneCaption(context, plan);
  const pngBlob = await canvasToBlob(canvas, "image/png");
  return {
    imageUrl: URL.createObjectURL(pngBlob),
    pngBlob
  };
}

function drawSceneBackground(context, plan) {
  const gradient = context.createLinearGradient(0, 0, 1200, 1200);
  const palette = getPalette(plan.geo.code);
  gradient.addColorStop(0, palette[0]);
  gradient.addColorStop(0.62, palette[1]);
  gradient.addColorStop(1, palette[2]);
  context.fillStyle = gradient;
  context.fillRect(0, 0, 1200, 1200);

  context.fillStyle = "rgba(255,255,255,0.42)";
  roundRect(context, 96, 120, 1008, 780, 28);
  context.fill();

  context.fillStyle = "rgba(24, 90, 61, 0.14)";
  for (let i = 0; i < 7; i += 1) {
    context.beginPath();
    context.arc(160 + i * 165, 980 + Math.sin(i) * 28, 86, 0, Math.PI * 2);
    context.fill();
  }
}

function drawProductHero(context, image) {
  context.save();
  context.shadowColor = "rgba(26, 36, 30, 0.22)";
  context.shadowBlur = 42;
  context.shadowOffsetY = 24;
  context.fillStyle = "rgba(255,255,255,0.92)";
  roundRect(context, 310, 250, 580, 580, 32);
  context.fill();
  context.restore();
  drawContainedImage(context, image, 360, 300, 480, 480);
}

function drawProductPlaceholder(context, metadata) {
  context.fillStyle = "rgba(255,255,255,0.92)";
  roundRect(context, 330, 285, 540, 500, 32);
  context.fill();
  context.fillStyle = "#2f7d5a";
  context.font = "800 46px system-ui";
  context.textAlign = "center";
  context.fillText(metadata.fileBaseName.split("-").slice(0, 2).join(" "), 600, 540);
}

function drawSceneCaption(context, plan) {
  context.fillStyle = "rgba(30, 37, 32, 0.82)";
  roundRect(context, 120, 930, 960, 126, 22);
  context.fill();
  context.fillStyle = "#ffffff";
  context.font = "800 42px system-ui";
  context.textAlign = "left";
  context.fillText(plan.sceneType.toUpperCase(), 168, 984);
  context.font = "500 28px system-ui";
  context.fillText(`${plan.geo.market} · ${plan.category}`, 168, 1028);
}

function drawChecker(context, width, height) {
  context.fillStyle = "#f8faf6";
  context.fillRect(0, 0, width, height);
  context.fillStyle = "#e9eee5";
  const size = 32;
  for (let y = 0; y < height; y += size) {
    for (let x = 0; x < width; x += size) {
      if ((x / size + y / size) % 2 === 0) context.fillRect(x, y, size, size);
    }
  }
}

function getPalette(code) {
  const palettes = {
    SG: ["#f6fbf5", "#b8d8c3", "#e55c4d"],
    PH: ["#fff7d6", "#7cc7b2", "#51a9d6"],
    IN: ["#fff1cf", "#e8a63d", "#198f88"],
    US: ["#f4f7fb", "#b7c8d8", "#82956f"],
    SEA: ["#f6fbef", "#9fcf9f", "#f08d6d"]
  };
  return palettes[code] || palettes.SEA;
}

function drawContainedImage(context, image, x, y, width, height) {
  const scale = Math.min(width / image.width, height / image.height);
  const drawWidth = image.width * scale;
  const drawHeight = image.height * scale;
  context.drawImage(image, x + (width - drawWidth) / 2, y + (height - drawHeight) / 2, drawWidth, drawHeight);
}

function roundRect(context, x, y, width, height, radius) {
  context.beginPath();
  context.moveTo(x + radius, y);
  context.arcTo(x + width, y, x + width, y + height, radius);
  context.arcTo(x + width, y + height, x, y + height, radius);
  context.arcTo(x, y + height, x, y, radius);
  context.arcTo(x, y, x + width, y, radius);
  context.closePath();
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = reject;
    image.src = src;
  });
}

function canvasToBlob(canvas, type, quality) {
  return new Promise((resolve) => canvas.toBlob(resolve, type, quality));
}

async function imageUrlToWebp(url) {
  const image = await loadImage(url);
  const canvas = document.createElement("canvas");
  canvas.width = 1200;
  canvas.height = 1200;
  const context = canvas.getContext("2d");
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.drawImage(image, 0, 0, canvas.width, canvas.height);
  return canvasToBlob(canvas, "image/webp", 0.86);
}

async function dataUrlToBlob(dataUrl) {
  const response = await fetch(dataUrl);
  return response.blob();
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",", 2)[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",", 2)[1]);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
