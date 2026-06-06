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
  metadata: [],
  categories: [],
  listingDraft: null,
  templateFields: [],
  catalogProducts: loadCatalogProducts(),
  catalogStatusFilter: "all",
  catalogQuery: ""
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
  resultSummary: document.querySelector("#resultSummary"),
  readinessPill: document.querySelector("#readinessPill"),
  readinessScore: document.querySelector("#readinessScore"),
  readinessFill: document.querySelector("#readinessFill"),
  missingFields: document.querySelector("#missingFields"),
  listingKeywords: document.querySelector("#listingKeywords"),
  listingHashtags: document.querySelector("#listingHashtags"),
  catalogRows: document.querySelector("#catalogRows"),
  catalogHealthScore: document.querySelector("#catalogHealthScore"),
  catalogHealthFill: document.querySelector("#catalogHealthFill"),
  catalogHealthText: document.querySelector("#catalogHealthText"),
  catalogStatusFilter: document.querySelector("#catalogStatusFilter"),
  catalogSearch: document.querySelector("#catalogSearch"),
  saveCatalogButton: document.querySelector("#saveCatalogButton"),
  exportTemplateButton: document.querySelector("#exportTemplateButton"),
  templateFieldCount: document.querySelector("#templateFieldCount"),
  backgroundIdeas: document.querySelector("#backgroundIdeas"),
  shopeeCategoryOptions: document.querySelector("#shopeeCategoryOptions"),
  inventoryToast: document.querySelector("#inventoryToast"),
  copyMetadataButton: document.querySelector("#copyMetadataButton"),
  exportTemplateXlsxButton: document.querySelector("#exportTemplateXlsxButton")
};

const fields = [
  "imageModel",
  "textModel",
  "productName",
  "category",
  "shopeeCategorySearch",
  "shopeeCategory",
  "brandTone",
  "audience",
  "productNote",
  "brand",
  "price",
  "stock",
  "weight",
  "dimensions",
  "backgroundPrompt",
  "targetGeo",
  "count",
  "listingTitle",
  "listingCategory",
  "listingDescription",
  "listingHighlights",
  "listingPrice",
  "listingStock"
]
  .reduce((items, id) => ({ ...items, [id]: document.querySelector(`#${id}`) }), {});

const PIPELINE_STEPS = [
  "Seller photo and metadata captured",
  "Product isolated into clean preview",
  "Preview variants polished",
  "Metadata JSON generated",
  "PNG, WebP, and metadata ZIP ready"
];

init();

async function init() {
  renderPipelineStatus(0);
  drawIsolationPlaceholder();
  await refreshApiStatus();
  await loadCategories();
  await loadTemplateFields();
  renderCatalog();
  els.productImage.addEventListener("change", handleImageUpload);
  els.generateButton.addEventListener("click", generateScenes);
  els.exportButton.addEventListener("click", exportZip);
  els.saveCatalogButton.addEventListener("click", saveCurrentListingToCatalog);
  els.exportTemplateButton.addEventListener("click", exportTemplateRow);
  els.copyMetadataButton.addEventListener("click", copyMetadataPayload);
  els.exportTemplateXlsxButton.addEventListener("click", exportTemplateXlsx);
  document.querySelectorAll("[data-tab-target]").forEach((button) => {
    button.addEventListener("click", () => activateTab(button.dataset.tabTarget));
  });
  fields.backgroundPrompt.addEventListener("focus", renderBackgroundIdeas);
  fields.backgroundPrompt.addEventListener("input", renderBackgroundIdeas);
  fields.backgroundPrompt.addEventListener("blur", () => {
    window.setTimeout(() => els.backgroundIdeas.classList.remove("is-visible"), 140);
  });
  for (const field of [fields.productName, fields.category, fields.brandTone, fields.audience, fields.targetGeo]) {
    field.addEventListener("input", () => {
      if (document.activeElement === fields.backgroundPrompt) renderBackgroundIdeas();
    });
    field.addEventListener("change", () => {
      if (document.activeElement === fields.backgroundPrompt) renderBackgroundIdeas();
    });
  }
  fields.shopeeCategorySearch.addEventListener("input", syncShopeeCategorySearch);
  fields.shopeeCategorySearch.addEventListener("change", syncShopeeCategorySearch);
  els.catalogStatusFilter.addEventListener("change", () => {
    state.catalogStatusFilter = els.catalogStatusFilter.value;
    renderCatalog();
  });
  els.catalogSearch.addEventListener("input", () => {
    state.catalogQuery = els.catalogSearch.value.trim().toLowerCase();
    renderCatalog();
  });
  for (const field of [fields.listingTitle, fields.listingPrice, fields.listingStock, fields.productName, fields.price, fields.stock, fields.weight, fields.dimensions]) {
    field.addEventListener("input", () => {
      if (state.listingDraft) upsertCurrentListingInCatalog();
      renderCatalog();
    });
  }
}

async function refreshApiStatus() {
  try {
    const response = await fetch("/api/health");
    const health = await response.json();
    populateModelSelect(fields.imageModel, health.imageModelOptions || [health.imageModel], health.imageModel);
    populateModelSelect(fields.textModel, health.textModelOptions || [health.textModel], health.textModel);
    els.apiStatus.textContent = health.openaiConfigured ? "OpenAI ready" : "Local fallback";
    els.apiStatus.classList.toggle("warn", !health.openaiConfigured);
  } catch {
    populateModelSelect(fields.imageModel, ["gpt-image-2", "gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"], "gpt-image-1.5");
    populateModelSelect(fields.textModel, ["gpt-5.5", "gpt-5.4-mini", "gpt-5.4-nano", "gpt-5.1"], "gpt-5.5");
    els.apiStatus.textContent = "Offline fallback";
    els.apiStatus.classList.add("warn");
  }
}

function populateModelSelect(select, options, selected) {
  select.innerHTML = "";
  for (const model of options.filter(Boolean)) {
    const option = document.createElement("option");
    option.value = model;
    option.textContent = model;
    option.selected = model === selected;
    select.append(option);
  }
}

async function loadCategories() {
  try {
    const response = await fetch("/api/categories");
    const payload = await response.json();
    state.categories = payload.categories || [];
    fields.shopeeCategory.value = "";
    els.shopeeCategoryOptions.innerHTML = "";
    for (const category of state.categories) {
      if (category.has_children) continue;
      const option = document.createElement("option");
      option.value = `${category.category_id} · ${category.display_path}`;
      els.shopeeCategoryOptions.append(option);
    }
  } catch {
    state.categories = [];
  }
}

function syncShopeeCategorySearch() {
  const query = fields.shopeeCategorySearch.value.trim().toLowerCase();
  const match = state.categories.find((category) => {
    const label = `${category.category_id} · ${category.display_path}`.toLowerCase();
    return label === query || String(category.category_id) === query;
  });
  fields.shopeeCategory.value = match ? String(match.category_id) : "";
  fields.category.value = match?.display_path || "";
}

async function loadTemplateFields() {
  try {
    const response = await fetch("/api/template-fields");
    const payload = await response.json();
    state.templateFields = payload.fields || [];
    const required = state.templateFields.filter((field) => field.requirement === "Mandatory").length;
    els.templateFieldCount.textContent = `${state.templateFields.length} columns parsed, ${required} mandatory`;
  } catch {
    state.templateFields = [];
    els.templateFieldCount.textContent = "Template parser unavailable";
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
  setProgress(0, state.productImages.length, "Photos uploaded. Click Polish previews to remove backgrounds.");
  renderPipelineStatus(1);
}

async function generateScenes() {
  activateTab("previews");
  els.generateButton.disabled = true;
  els.exportButton.disabled = true;
  els.generateButton.textContent = "Polishing...";
  renderPipelineStatus(state.productImages.length ? 1 : 0);

  const input = getInput();
  const localPayload = buildGenerationPayload(input);
  if (state.productImages.length && !state.isolatedImages.length) {
    setProgress(0, state.productImages.length, "Removing backgrounds...");
    await removeBackgrounds();
    renderUploadStrip();
    drawIsolationPreview();
    renderPipelineStatus(2);
  }
  const productImages = await getProductReferencePayloads();
  state.metadata = localPayload.metadata;
  state.scenes = [];
  renderScenes();
  setProgress(0, localPayload.plans.length, `Polished 0 of ${localPayload.plans.length} previews`);

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
    setProgress(index + 1, localPayload.plans.length, `Polished ${index + 1} of ${localPayload.plans.length} previews`);
  }

  await generateListingDraft(productImages);
  renderMetadata();
  renderPipelineStatus(5);
  els.resultSummary.textContent = `${state.scenes.length} product previews ready`;
  els.exportButton.disabled = false;
  els.generateButton.disabled = false;
  els.generateButton.textContent = "Polish previews";
}

async function generateListingDraft(productImages) {
  setProgress(0, 1, "Drafting product listing...");
  try {
    const selectedCategory = selectedShopeeCategory();
    const response = await fetch("/api/generate-listing-draft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...getInput(),
        productImages,
        imagesCount: state.productImages.length,
        categoryId: selectedCategory?.category_id || null,
        categoryPath: selectedCategory?.display_path || "",
        categoryConfirmed: Boolean(selectedCategory),
        confirmedFields: selectedCategory ? ["category"] : []
      })
    });
    state.listingDraft = await response.json();
  } catch (error) {
    state.listingDraft = buildLocalListingDraft(error.message);
  }
  renderListingDraft();
  setProgress(1, 1, "Product listing draft ready");
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
      body: JSON.stringify({ images, imageModel: fields.imageModel.value })
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

function activateTab(tabName) {
  document.querySelectorAll("[data-tab-panel]").forEach((panel) => {
    panel.classList.toggle("is-active", panel.dataset.tabPanel === tabName);
  });
  document.querySelectorAll("[data-tab-target]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tabTarget === tabName);
  });
}

function renderBackgroundIdeas() {
  const ideas = buildBackgroundIdeas();
  els.backgroundIdeas.innerHTML = "";
  for (const idea of ideas) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = idea;
    button.addEventListener("click", () => {
      fields.backgroundPrompt.value = idea;
      els.backgroundIdeas.classList.remove("is-visible");
    });
    els.backgroundIdeas.append(button);
  }
  els.backgroundIdeas.classList.toggle("is-visible", document.activeElement === fields.backgroundPrompt);
}

function buildBackgroundIdeas() {
  const product = fields.productName.value || "product";
  const category = selectedShopeeCategory()?.display_path || fields.category.value || "marketplace product";
  const tone = fields.brandTone.value || "clean and trustworthy";
  const audience = fields.audience.value || "online shoppers";
  const geo = fields.targetGeo.options[fields.targetGeo.selectedIndex]?.textContent || "Singapore";
  return [
    `${product} in a bright ${geo} apartment setting with polished retail lighting, tidy props, and ${tone} styling for ${audience}.`,
    `${category} on a clean marketplace hero surface with soft natural shadows, subtle regional decor cues, and generous whitespace.`,
    `${product} in a commercial lifestyle scene tailored to ${geo}, premium but realistic, with the original product centered and unchanged.`,
    `${category} on a seasonal gift-ready setup with warm daylight, neat packaging cues, and marketplace-safe background details.`
  ];
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
    listing: exportListingPayload(),
    images: state.metadata
  }, null, 2);
}

function renderListingDraft() {
  const draft = state.listingDraft;
  if (!draft?.listing_draft) return;

  const listing = draft.listing_draft;
  const categoryValue = listing.category?.value || {};
  fields.listingTitle.value = listing.title?.value || "";
  fields.listingCategory.value = categoryValue.category_id
    ? `${categoryValue.category_id} · ${categoryValue.category_path}`
    : "";
  fields.listingDescription.value = listing.description?.value || "";
  fields.listingHighlights.value = (listing.highlights || []).map((item) => item.value).join("\n");
  fields.listingPrice.value = listing.price?.value || fields.price.value || "";
  fields.listingStock.value = listing.stock?.value || fields.stock.value || "";

  const readiness = draft.readiness || { score: 0, status: "Needs Review" };
  els.readinessScore.textContent = `${readiness.score || 0}/100`;
  els.readinessFill.style.width = `${readiness.score || 0}%`;
  els.readinessPill.textContent = readiness.status || "Needs Review";
  els.readinessPill.classList.toggle("warn", readiness.status !== "Ready to Export");
  renderTags(els.listingKeywords, listing.keywords || []);
  renderTags(els.listingHashtags, listing.hashtags || []);
  renderMissingFields(draft.missing_fields || []);
  els.saveCatalogButton.disabled = false;
  els.exportTemplateButton.disabled = false;
  upsertCurrentListingInCatalog();
  renderCatalog();
}

function renderMissingFields(items) {
  els.missingFields.innerHTML = "";
  if (!items.length) {
    els.missingFields.innerHTML = `<div class="missing-item"><b>No blocking missing fields</b><span>Review the draft before export.</span></div>`;
    return;
  }
  for (const item of items) {
    const node = document.createElement("div");
    node.className = "missing-item";
    node.innerHTML = `<b>${escapeHtml(item.field)} · ${escapeHtml(item.importance)}</b><span>${escapeHtml(item.reason)}</span>`;
    els.missingFields.append(node);
  }
}

function renderTags(container, tags) {
  container.innerHTML = "";
  for (const tag of tags) {
    const node = document.createElement("span");
    node.textContent = tag;
    container.append(node);
  }
}

async function exportZip() {
  if (!state.scenes.length) return;
  els.exportButton.disabled = true;
  els.exportButton.textContent = "Bundling...";
  const listingPayload = exportListingPayload();
  const templateExport = await buildTemplateExport(listingPayload);
  const templateWorkbook = await buildTemplateWorkbook(listingPayload);

  const files = [
    {
      name: "metadata.json",
      data: JSON.stringify({
        generatedAt: new Date().toISOString(),
        listing: listingPayload,
        images: state.metadata
      }, null, 2)
    },
    {
      name: "product_listing.json",
      data: JSON.stringify(listingPayload, null, 2)
    },
    {
      name: "shopee_template_row.tsv",
      data: templateExport.tsv
    },
    {
      name: "shopee_template_row.json",
      data: JSON.stringify({ fields: templateExport.fields, row: templateExport.row }, null, 2)
    },
    {
      name: "shopee_template.xlsx",
      data: new Uint8Array(await templateWorkbook.arrayBuffer())
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

async function exportTemplateRow() {
  els.exportTemplateButton.disabled = true;
  els.exportTemplateButton.textContent = "Exporting...";
  const templateExport = await buildTemplateExport(exportListingPayload());
  downloadText(`${slugify(fields.productName.value || "product")}-shopee-template-row.tsv`, templateExport.tsv, "text/tab-separated-values");
  els.exportTemplateButton.disabled = false;
  els.exportTemplateButton.textContent = "Export template row";
}

async function exportTemplateXlsx() {
  els.exportTemplateXlsxButton.disabled = true;
  els.exportTemplateXlsxButton.textContent = "Exporting...";
  const workbook = await buildTemplateWorkbook(exportListingPayload());
  const url = URL.createObjectURL(workbook);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${slugify(fields.productName.value || "product")}-shopee-template.xlsx`;
  link.click();
  URL.revokeObjectURL(url);
  els.exportTemplateXlsxButton.disabled = false;
  els.exportTemplateXlsxButton.textContent = "Export template .xlsx";
}

async function buildTemplateWorkbook(listingPayload) {
  const response = await fetch("/api/export-template-xlsx", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(listingPayload)
  });
  if (!response.ok) throw new Error("Template workbook export failed");
  return response.blob();
}

async function buildTemplateExport(listingPayload) {
  try {
    const response = await fetch("/api/map-template-row", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(listingPayload)
    });
    if (!response.ok) throw new Error("Template mapping failed");
    return response.json();
  } catch {
    const fieldsToExport = state.templateFields.length
      ? state.templateFields
      : [
        { key: "ps_category", label: "Category" },
        { key: "ps_product_name", label: "Product Name" },
        { key: "ps_product_description", label: "Product Description" },
        { key: "ps_price", label: "Price" },
        { key: "ps_stock", label: "Stock" },
        { key: "ps_item_cover_image", label: "Cover image" }
      ];
    const row = mapListingToTemplateRowFallback(listingPayload, fieldsToExport);
    return {
      fields: fieldsToExport,
      row,
      tsv: `${fieldsToExport.map((field) => field.label).join("\t")}\n${fieldsToExport.map((field) => escapeTsv(row[field.key] || "")).join("\t")}`
    };
  }
}

function getInput() {
  const category = selectedShopeeCategory();
  return {
    imageModel: fields.imageModel.value,
    textModel: fields.textModel.value,
    productName: fields.productName.value,
    category: fields.category.value,
    productNote: fields.productNote.value,
    categoryHint: fields.category.value,
    categoryId: category?.category_id || null,
    categoryPath: category?.display_path || "",
    categoryConfirmed: Boolean(category),
    brandTone: fields.brandTone.value,
    brand: fields.brand.value,
    audience: fields.audience.value,
    price: fields.price.value,
    stock: fields.stock.value,
    weight: fields.weight.value,
    dimensions: fields.dimensions.value,
    backgroundPrompt: fields.backgroundPrompt.value,
    targetGeo: fields.targetGeo.value,
    count: Number(fields.count.value) || 8
  };
}

function selectedShopeeCategory() {
  const selectedId = Number(fields.shopeeCategory.value);
  if (!selectedId) return null;
  return state.categories.find((category) => category.category_id === selectedId) || null;
}

function exportListingPayload() {
  const listing = state.listingDraft?.listing_draft || {};
  const readiness = state.listingDraft?.readiness || { score: 0, status: "Needs Review", suggestions: [] };
  const category = listing.category?.value || selectedShopeeCategory() || {};
  const missing = state.listingDraft?.missing_fields || [];
  const dimensions = parseDimensionInput(fields.dimensions.value);
  return {
    exported_at: new Date().toISOString(),
    platform: "Marketplace",
    target_market: fields.targetGeo.value,
    models: {
      image: fields.imageModel.value,
      text: fields.textModel.value
    },
    background_prompt: fields.backgroundPrompt.value,
    ready_for_upload: readiness.status === "Ready to Export",
    readiness: {
      score: readiness.score || 0,
      status: readiness.status || "Needs Review",
      missing_required_fields: missing.filter((item) => item.importance === "required").map((item) => item.field),
      missing_recommended_fields: missing.filter((item) => item.importance === "recommended").map((item) => item.field)
    },
    listing: {
      product_name: fields.listingTitle.value || listing.title?.value || fields.productName.value,
      category_id: category.category_id || null,
      category_path: category.category_path || category.display_path || "",
      category_confirmed: Boolean(selectedShopeeCategory()),
      description: fields.listingDescription.value || listing.description?.value || "",
      brand: fields.brand.value,
      price: fields.listingPrice.value || fields.price.value,
      stock: fields.listingStock.value || fields.stock.value,
      weight: fields.weight.value || listing.weight?.value || "",
      length: dimensions.length,
      width: dimensions.width,
      height: dimensions.height,
      attributes: listing.attributes || {},
      variations: listing.variations || []
    },
    logistics: {
      weight: fields.weight.value || listing.weight?.value || "",
      dimensions_text: fields.dimensions.value,
      length: dimensions.length,
      width: dimensions.width,
      height: dimensions.height,
      shipping_channel: "On"
    },
    images: {
      main_image: state.scenes[0]?.metadata?.fileBaseName ? `png/${state.scenes[0].metadata.fileBaseName}.png` : "",
      gallery_images: state.scenes.slice(1).map((scene) => `png/${scene.metadata.fileBaseName}.png`),
      alt_text: listing.alt_text?.value || state.metadata[0]?.altText || ""
    },
    seo: {
      keywords: listing.keywords || [],
      hashtags: listing.hashtags || []
    },
    warnings: [
      "Final manual review in the seller platform may still be required."
    ]
  };
}

function seedCatalogProducts() {
  return [
    {
      id: "sample-powerbank",
      name: "Compact Fast Charge Power Bank",
      category: "Electronics & Gadgets",
      price: "24.90",
      stock: "85",
      status: "Ready to Export",
      readiness: 92,
      imageUrl: "",
      source: "sample"
    },
    {
      id: "sample-serum",
      name: "Brightening Vitamin C Serum",
      category: "Health & Beauty",
      price: "18.50",
      stock: "42",
      status: "Needs Review",
      readiness: 68,
      imageUrl: "",
      source: "sample"
    },
    {
      id: "sample-massager",
      name: "Mini Facial Massage Tool",
      category: "Health & Beauty",
      price: "",
      stock: "",
      status: "Draft",
      readiness: 38,
      imageUrl: "",
      source: "sample"
    }
  ];
}

function loadCatalogProducts() {
  try {
    const stored = JSON.parse(localStorage.getItem("shopshotCatalogProducts") || "null");
    if (Array.isArray(stored) && stored.length) return stored;
  } catch {
    return seedCatalogProducts();
  }
  return seedCatalogProducts();
}

function saveCatalogProducts() {
  const persisted = state.catalogProducts.map(({ payload, ...product }) => product);
  localStorage.setItem("shopshotCatalogProducts", JSON.stringify(persisted));
}

function upsertCurrentListingInCatalog() {
  const payload = exportListingPayload();
  const listing = payload.listing;
  const current = {
    id: "current-listing",
    name: listing.product_name || fields.productName.value || "Current product",
    category: listing.category_path || selectedShopeeCategory()?.display_path || fields.category.value || "Category pending",
    price: listing.price || "",
    stock: listing.stock || "",
    status: payload.readiness.status || "Needs Review",
    readiness: payload.readiness.score || 0,
    imageUrl: state.scenes[0]?.imageUrl || state.productImages[0]?.isolatedUrl || state.productImages[0]?.sourceUrl || "",
    source: "current",
    payload
  };
  const index = state.catalogProducts.findIndex((product) => product.id === current.id);
  if (index >= 0) {
    state.catalogProducts[index] = current;
  } else {
    state.catalogProducts.unshift(current);
  }
  saveCatalogProducts();
}

function saveCurrentListingToCatalog() {
  if (!state.listingDraft) return;
  upsertCurrentListingInCatalog();
  renderCatalog();
  els.inventoryToast.textContent = "Added to Inventory";
  window.setTimeout(() => {
    els.inventoryToast.textContent = "";
  }, 2400);
  activateTab("exports");
}

async function copyMetadataPayload() {
  const payload = els.metadataPreview.textContent || "{}";
  try {
    await navigator.clipboard.writeText(payload);
    els.copyMetadataButton.textContent = "Copied";
  } catch {
    const textarea = document.createElement("textarea");
    textarea.value = payload;
    document.body.append(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
    els.copyMetadataButton.textContent = "Copied";
  }
  window.setTimeout(() => {
    els.copyMetadataButton.textContent = "Copy";
  }, 1800);
}

function renderCatalog() {
  const products = filteredCatalogProducts();
  const average = state.catalogProducts.length
    ? Math.round(state.catalogProducts.reduce((total, product) => total + product.readiness, 0) / state.catalogProducts.length)
    : 0;
  const readyCount = state.catalogProducts.filter((product) => product.status === "Ready to Export").length;
  const reviewCount = state.catalogProducts.filter((product) => product.status !== "Ready to Export").length;

  els.catalogHealthScore.textContent = `${average}%`;
  els.catalogHealthFill.style.width = `${average}%`;
  els.catalogHealthText.textContent = `${readyCount} ready, ${reviewCount} need review across ${state.catalogProducts.length} products`;
  els.catalogRows.innerHTML = "";

  if (!products.length) {
    els.catalogRows.innerHTML = `<div class="catalog-empty">No products match this filter.</div>`;
    return;
  }

  for (const product of products) {
    const row = document.createElement("article");
    row.className = "catalog-table catalog-row";
    row.innerHTML = `
      <span class="catalog-thumb">${product.imageUrl ? `<img src="${escapeHtml(product.imageUrl)}" alt="">` : initials(product.name)}</span>
      <span><b>${escapeHtml(product.name)}</b><small>${product.source === "current" ? "Current listing" : "Catalog item"}</small></span>
      <span>${escapeHtml(product.category || "Unmapped")}</span>
      <span>${product.price ? `$${escapeHtml(product.price)}` : "Missing"}</span>
      <span>${product.stock || product.stock === 0 ? escapeHtml(product.stock) : "Missing"}</span>
      <span><em class="${product.status === "Ready to Export" ? "ready" : "warn"}">${escapeHtml(product.status)}</em></span>
      <span class="catalog-readiness"><i><b style="width:${product.readiness}%"></b></i>${product.readiness}%</span>
    `;
    els.catalogRows.append(row);
  }
}

function filteredCatalogProducts() {
  return state.catalogProducts.filter((product) => {
    const statusMatches = state.catalogStatusFilter === "all" || product.status === state.catalogStatusFilter;
    const haystack = `${product.name} ${product.category} ${product.status}`.toLowerCase();
    const queryMatches = !state.catalogQuery || haystack.includes(state.catalogQuery);
    return statusMatches && queryMatches;
  });
}

function mapListingToTemplateRowFallback(payload, fieldsToExport) {
  const listing = payload.listing || {};
  const images = payload.images || {};
  const row = Object.fromEntries(fieldsToExport.map((field) => [field.key, ""]));
  row.ps_category = listing.category_id || "";
  row.ps_product_name = listing.product_name || "";
  row.ps_product_description = listing.description || "";
  row.ps_price = listing.price || "";
  row.ps_stock = listing.stock || "";
  row.ps_item_cover_image = images.main_image || "";
  row.ps_weight = payload.logistics?.weight || listing.weight || "";
  row.ps_length = payload.logistics?.length || listing.length || "";
  row.ps_width = payload.logistics?.width || listing.width || "";
  row.ps_height = payload.logistics?.height || listing.height || "";
  row["channel_id.1000"] = payload.logistics?.shipping_channel || "On";
  (images.gallery_images || []).slice(0, 8).forEach((image, index) => {
    const key = `ps_item_image_${index + 1}`;
    if (key in row) row[key] = image;
  });
  return row;
}

function initials(value) {
  return String(value || "P")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("") || "P";
}

function parseDimensionInput(value) {
  const numbers = String(value || "").match(/\d+(?:\.\d+)?/g) || [];
  return {
    length: numbers[0] || "",
    width: numbers[1] || "",
    height: numbers[2] || ""
  };
}

function buildLocalListingDraft(reason) {
  const category = selectedShopeeCategory();
  const missing = [];
  const dimensions = parseDimensionInput(fields.dimensions.value);
  if (!fields.productName.value) missing.push({ field: "product_name", importance: "required", reason: "Add a product name for the upload template." });
  if (!fields.price.value) missing.push({ field: "price", importance: "required", reason: "Add seller-provided product price." });
  if (!fields.stock.value) missing.push({ field: "stock", importance: "required", reason: "Add seller-provided available stock for the upload template." });
  if (!fields.weight.value) missing.push({ field: "weight", importance: "required", reason: "Add product weight for the template logistics column." });
  if (!dimensions.length) missing.push({ field: "length", importance: "required", reason: "Add product length in the dimensions field." });
  if (!dimensions.width) missing.push({ field: "width", importance: "required", reason: "Add product width in the dimensions field." });
  if (!dimensions.height) missing.push({ field: "height", importance: "required", reason: "Add product height in the dimensions field." });
  if (!category) missing.push({ field: "marketplace_category", importance: "recommended", reason: "Confirm the best marketplace category before upload when available." });
  missing.push({ field: "dimensions", importance: "recommended", reason: "Exact dimensions are not visible from image." });
  const ready = Boolean(fields.productName.value && fields.price.value && fields.stock.value && fields.weight.value && dimensions.length && dimensions.width && dimensions.height);
  return {
    mode: "local",
    product_profile: {
      detected_product_type: { value: fields.category.value || fields.productName.value, source: "inferred", confidence: "low", needs_user_review: true },
      uncertain_details: [reason]
    },
    listing_draft: {
      title: { value: `${fields.productName.value} | Marketplace Ready`, source: "generated", confidence: "low", needs_user_review: true },
      category: { value: category ? { category_id: category.category_id, category_path: category.display_path } : { category_id: null, category_path: "" }, source: category ? "provided" : "missing", confidence: category ? "high" : "low", needs_user_review: !category },
      description: { value: `${fields.productName.value} prepared for listing review. Please confirm price, stock, category, and product details before publishing.`, source: "generated", confidence: "low", needs_user_review: true },
      highlights: [
        { value: "Polished product preview images included", source: "generated", confidence: "medium", needs_user_review: true },
        { value: "Review all generated details before export", source: "generated", confidence: "medium", needs_user_review: true }
      ],
      keywords: [fields.productName.value, fields.category.value, "marketplace"].filter(Boolean),
      hashtags: [`#${slugify(fields.productName.value).replaceAll("-", "")}`, "#ecommerce"].filter((tag) => tag.length > 1),
      alt_text: { value: `${fields.productName.value} product preview`, source: "generated", confidence: "low", needs_user_review: true },
      price: { value: fields.price.value, source: fields.price.value ? "provided" : "missing", confidence: fields.price.value ? "high" : "low", needs_user_review: !fields.price.value },
      stock: { value: fields.stock.value, source: fields.stock.value ? "provided" : "missing", confidence: fields.stock.value ? "high" : "low", needs_user_review: !fields.stock.value },
      weight: { value: fields.weight.value, source: fields.weight.value ? "provided" : "missing", confidence: fields.weight.value ? "high" : "low", needs_user_review: !fields.weight.value },
      dimensions: { value: dimensions, source: ready ? "provided" : "missing", confidence: "medium", needs_user_review: !ready },
      attributes: {},
      variations: []
    },
    missing_fields: missing,
    readiness: {
      score: ready ? 80 : 45,
      status: ready ? "Ready to Export" : "Needs Review",
      suggestions: missing.map((item) => item.reason)
    }
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

function downloadText(filename, data, type = "text/plain") {
  const blob = new Blob([data], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function escapeTsv(value) {
  const text = String(value ?? "");
  if (!/[\t\n"]/.test(text)) return text;
  return `"${text.replaceAll('"', '""')}"`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
