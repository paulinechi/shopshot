const pageSize = 4;
const catalogTotal = 128;

const products = [
  {
    id: 1,
    name: "Pro Audio Studio Headphones X1",
    sku: "PA-X1-BLK",
    category: "electronics",
    categoryLabel: "Electronics",
    price: 299,
    status: "ready",
    statusLabel: "Ready",
    readiness: 95,
    thumb: "headphones",
  },
  {
    id: 2,
    name: "Minimalist Ceramic Watch",
    sku: "CW-MINI-04",
    category: "fashion",
    categoryLabel: "Fashion",
    price: 145,
    status: "review",
    statusLabel: "Needs Review",
    readiness: 62,
    thumb: "watch",
  },
  {
    id: 3,
    name: "Retro 35mm Film Camera",
    sku: "CAM-R35-VNTG",
    category: "electronics",
    categoryLabel: "Electronics",
    price: 580,
    status: "draft",
    statusLabel: "Draft",
    readiness: 28,
    thumb: "camera",
  },
  {
    id: 4,
    name: "Red Hyper-Run Sneakers",
    sku: "FT-HYPER-01",
    category: "fashion",
    categoryLabel: "Fashion",
    price: 120,
    status: "ready",
    statusLabel: "Ready",
    readiness: 88,
    thumb: "sneaker",
  },
  {
    id: 5,
    name: "Aura Desk Lamp Mini",
    sku: "HM-AURA-12",
    category: "home",
    categoryLabel: "Home",
    price: 78,
    status: "review",
    statusLabel: "Needs Review",
    readiness: 54,
    thumb: "lamp",
  },
  {
    id: 6,
    name: "Everyday Canvas Tote",
    sku: "FS-TOTE-22",
    category: "fashion",
    categoryLabel: "Fashion",
    price: 42,
    status: "ready",
    statusLabel: "Ready",
    readiness: 91,
    thumb: "tote",
  },
  {
    id: 7,
    name: "Pulse Smart Bottle",
    sku: "HM-PULSE-08",
    category: "home",
    categoryLabel: "Home",
    price: 65,
    status: "draft",
    statusLabel: "Draft",
    readiness: 33,
    thumb: "bottle",
  },
  {
    id: 8,
    name: "Compact Travel Drone Air",
    sku: "EL-DRONE-19",
    category: "electronics",
    categoryLabel: "Electronics",
    price: 799,
    status: "review",
    statusLabel: "Needs Review",
    readiness: 71,
    thumb: "drone",
  },
  {
    id: 9,
    name: "Slate Leather Wallet",
    sku: "FS-WLT-11",
    category: "fashion",
    categoryLabel: "Fashion",
    price: 58,
    status: "ready",
    statusLabel: "Ready",
    readiness: 89,
    thumb: "wallet",
  },
  {
    id: 10,
    name: "Nova Ceramic Mug Set",
    sku: "HM-MUG-03",
    category: "home",
    categoryLabel: "Home",
    price: 36,
    status: "review",
    statusLabel: "Needs Review",
    readiness: 57,
    thumb: "mug",
  },
  {
    id: 11,
    name: "Air Note Bluetooth Keyboard",
    sku: "EL-KEY-81",
    category: "electronics",
    categoryLabel: "Electronics",
    price: 110,
    status: "draft",
    statusLabel: "Draft",
    readiness: 30,
    thumb: "keyboard",
  },
  {
    id: 12,
    name: "Core Motion Running Vest",
    sku: "FT-VEST-07",
    category: "fashion",
    categoryLabel: "Fashion",
    price: 95,
    status: "ready",
    statusLabel: "Ready",
    readiness: 87,
    thumb: "vest",
  },
];

const state = {
  screen: "catalog",
  query: "",
  status: "all",
  category: "all",
  page: 1,
  selected: new Set([2]),
  settings: {
    autoDescriptions: true,
    readinessAlerts: true,
    autoExport: false,
  },
};

const pageTitle = document.getElementById("pageTitle");
const searchInput = document.getElementById("searchInput");
const statusFilter = document.getElementById("statusFilter");
const categoryFilter = document.getElementById("categoryFilter");
const clearFilters = document.getElementById("clearFilters");
const exportButton = document.getElementById("exportButton");
const productRows = document.getElementById("productRows");
const pagination = document.getElementById("pagination");
const resultsSummary = document.getElementById("resultsSummary");
const selectAll = document.getElementById("selectAll");
const assistantMessage = document.getElementById("assistantMessage");
const copilotStatus = document.getElementById("copilotStatus");
const assistantContext = document.getElementById("assistantContext");
const insightText = document.getElementById("insightText");
const healthScore = document.getElementById("healthScore");
const healthBarFill = document.getElementById("healthBarFill");
const assistantForm = document.getElementById("assistantForm");
const assistantPrompt = document.getElementById("assistantPrompt");
const quickActions = document.getElementById("quickActions");
const actionReviewLabel = document.getElementById("actionReviewLabel");
const actionOptimizeLabel = document.getElementById("actionOptimizeLabel");
const actionCategoriesLabel = document.getElementById("actionCategoriesLabel");
const navLinks = Array.from(document.querySelectorAll(".nav-link[data-screen]"));
const topTabs = Array.from(document.querySelectorAll(".tab[data-screen]"));
const screens = Array.from(document.querySelectorAll("[data-screen-panel]"));
const openCreateButton = document.getElementById("openCreateButton");
const listingForm = document.getElementById("listingForm");
const listingName = document.getElementById("listingName");
const listingCategory = document.getElementById("listingCategory");
const listingChannel = document.getElementById("listingChannel");
const listingPrice = document.getElementById("listingPrice");
const listingHighlights = document.getElementById("listingHighlights");
const previewTitle = document.getElementById("previewTitle");
const previewDescription = document.getElementById("previewDescription");
const previewSeo = document.getElementById("previewSeo");
const previewReadiness = document.getElementById("previewReadiness");
const previewMissing = document.getElementById("previewMissing");
const createProgressValue = document.getElementById("createProgressValue");
const insightPriorityCount = document.getElementById("insightPriorityCount");
const insightRecommendations = document.getElementById("insightRecommendations");
const settingsToggles = document.getElementById("settingsToggles");
const supportResponse = document.getElementById("supportResponse");

const screenTitles = {
  catalog: "Catalog",
  insights: "AI Insights",
  create: "Create Listing",
  settings: "Settings",
  support: "Support",
};

const copilotConfig = {
  catalog: {
    status: "Active Analysis",
    context: "RKLES Assistant",
    actions: {
      review: "Fix all high-priority items",
      optimize: "Optimize descriptions",
      categories: "Check categories",
    },
  },
  insights: {
    status: "Trend Review",
    context: "Insights Assistant",
    message:
      "I’m tracking the biggest readiness movers across your catalog. I can turn this into a cleanup plan, explain the trend, or suggest the next best fix.",
    actions: {
      review: "Build cleanup plan",
      optimize: "Explain weekly lift",
      categories: "Show risk areas",
    },
  },
  create: {
    status: "Draft Coaching",
    context: "Listing Assistant",
    message:
      "I’m watching the draft as you edit. I can help sharpen the title, improve conversion copy, or point out what’s still missing before publish.",
    actions: {
      review: "Improve draft quality",
      optimize: "Rewrite title",
      categories: "Check missing fields",
    },
  },
  settings: {
    status: "Workspace Audit",
    context: "Settings Assistant",
    message:
      "These controls shape how ShopShot works behind the scenes. I can help you tune automation, alerts, and export behavior without overcomplicating the workflow.",
    actions: {
      review: "Recommend defaults",
      optimize: "Reduce manual work",
      categories: "Review channel setup",
    },
  },
  support: {
    status: "Help Routing",
    context: "Support Assistant",
    message:
      "I can route you toward the fastest fix based on whether the issue is export, content quality, or catalog cleanup.",
    actions: {
      review: "Troubleshoot export",
      optimize: "Improve content quality",
      categories: "Audit catalog issues",
    },
  },
};

function svgThumb(kind) {
  const art = {
    headphones: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#f8f8f9"/>
            <stop offset="1" stop-color="#d7d8db"/>
          </linearGradient>
        </defs>
        <rect width="60" height="60" rx="18" fill="url(#g)"/>
        <path d="M18 31a12 12 0 1124 0" fill="none" stroke="#272d37" stroke-width="4" stroke-linecap="round"/>
        <rect x="13" y="29" width="10" height="16" rx="5" fill="#1f232a"/>
        <rect x="37" y="29" width="10" height="16" rx="5" fill="#1f232a"/>
        <path d="M19 43c4 4 18 4 22 0" fill="none" stroke="#4b525f" stroke-width="2.4" stroke-linecap="round"/>
      </svg>`,
    watch: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#0d1c22"/>
            <stop offset="1" stop-color="#a0bbc0"/>
          </linearGradient>
        </defs>
        <rect width="60" height="60" rx="18" fill="url(#g)"/>
        <path d="M14 45L46 20" stroke="rgba(255,255,255,.28)" stroke-width="5"/>
        <rect x="22.5" y="27" width="15" height="7" rx="3.5" fill="#edf2f2"/>
        <circle cx="30" cy="30.5" r="5.2" fill="#cfd6d5"/>
        <circle cx="30" cy="30.5" r="3.5" fill="#899597"/>
        <path d="M30 30.5l2.6-1.4" stroke="#eef4f4" stroke-width="1.3" stroke-linecap="round"/>
      </svg>`,
    camera: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#1d120b"/>
            <stop offset="1" stop-color="#aa6f39"/>
          </linearGradient>
        </defs>
        <rect width="60" height="60" rx="18" fill="url(#g)"/>
        <rect x="12" y="22" width="36" height="20" rx="4" fill="#262730"/>
        <rect x="17" y="18" width="10" height="6" rx="2" fill="#3c3f47"/>
        <circle cx="31" cy="32" r="8" fill="#71757d"/>
        <circle cx="31" cy="32" r="5" fill="#10141e"/>
        <circle cx="44" cy="27" r="2" fill="#d8a24a"/>
        <path d="M12 42h36" stroke="rgba(255,255,255,.18)" stroke-width="1.6"/>
      </svg>`,
    sneaker: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#0d2630"/>
            <stop offset="1" stop-color="#8ae4f0"/>
          </linearGradient>
        </defs>
        <rect width="60" height="60" rx="18" fill="url(#g)"/>
        <path d="M12 36c9-1 14-10 18-17 3 6 8 10 16 12 2 1 4 3 4 6v2H12v-3z" fill="#d62828"/>
        <path d="M16 39h32" stroke="#f5f8fa" stroke-width="2.2" stroke-linecap="round"/>
        <path d="M28 24l4 3m-7 1l4 3m-7 1l4 3" stroke="#f2d5d5" stroke-width="1.3" stroke-linecap="round"/>
      </svg>`,
    lamp: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#ffefc0"/>
            <stop offset="1" stop-color="#f2f0df"/>
          </linearGradient>
        </defs>
        <rect width="60" height="60" rx="18" fill="url(#g)"/>
        <path d="M30 13l10 12H20L30 13z" fill="#ffe08c"/>
        <path d="M30 25v13" stroke="#6c6250" stroke-width="2"/>
        <path d="M22 42h16" stroke="#6c6250" stroke-width="2.6" stroke-linecap="round"/>
        <circle cx="30" cy="31" r="2.5" fill="#ffd76c"/>
      </svg>`,
    tote: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#d7cab8"/>
            <stop offset="1" stop-color="#faf4ed"/>
          </linearGradient>
        </defs>
        <rect width="60" height="60" rx="18" fill="url(#g)"/>
        <path d="M18 23h24l-2 22H20l-2-22z" fill="#b99f7d"/>
        <path d="M24 23c0-4 2.2-6 6-6s6 2 6 6" fill="none" stroke="#8e785f" stroke-width="2.2" stroke-linecap="round"/>
      </svg>`,
    bottle: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#224960"/>
            <stop offset="1" stop-color="#9fddff"/>
          </linearGradient>
        </defs>
        <rect width="60" height="60" rx="18" fill="url(#g)"/>
        <rect x="25" y="13" width="10" height="8" rx="2" fill="#c3efff"/>
        <path d="M24 21h12v7l4 17H20l4-17v-7z" fill="#dff6ff"/>
        <path d="M24 28h12" stroke="#90c9db" stroke-width="2"/>
      </svg>`,
    drone: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#2d3138"/>
            <stop offset="1" stop-color="#bcc4d5"/>
          </linearGradient>
        </defs>
        <rect width="60" height="60" rx="18" fill="url(#g)"/>
        <circle cx="18" cy="22" r="5" fill="#2a2f35"/>
        <circle cx="42" cy="22" r="5" fill="#2a2f35"/>
        <circle cx="18" cy="38" r="5" fill="#2a2f35"/>
        <circle cx="42" cy="38" r="5" fill="#2a2f35"/>
        <rect x="24" y="25" width="12" height="10" rx="4" fill="#eef1f6"/>
        <path d="M23 28H13m24 0h10M23 32H13m24 0h10" stroke="#636c79" stroke-width="1.7" stroke-linecap="round"/>
      </svg>`,
    wallet: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#41424b"/>
            <stop offset="1" stop-color="#8f95a4"/>
          </linearGradient>
        </defs>
        <rect width="60" height="60" rx="18" fill="url(#g)"/>
        <path d="M15 21h26a4 4 0 014 4v15H19a4 4 0 01-4-4V21z" fill="#22252b"/>
        <rect x="32" y="29" width="13" height="8" rx="4" fill="#3b4049"/>
        <circle cx="37" cy="33" r="1.5" fill="#b8bec9"/>
      </svg>`,
    mug: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#f8f5ef"/>
            <stop offset="1" stop-color="#d8cdc0"/>
          </linearGradient>
        </defs>
        <rect width="60" height="60" rx="18" fill="url(#g)"/>
        <rect x="17" y="22" width="20" height="20" rx="4" fill="#f4eee6"/>
        <path d="M37 25h4a5 5 0 010 10h-4" fill="none" stroke="#c7b8a4" stroke-width="2.4"/>
        <path d="M24 18c0 2-2 3-2 5m7-5c0 2-2 3-2 5" stroke="#dfd7ca" stroke-width="1.6" stroke-linecap="round"/>
      </svg>`,
    keyboard: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#edf0f7"/>
            <stop offset="1" stop-color="#c8cfdf"/>
          </linearGradient>
        </defs>
        <rect width="60" height="60" rx="18" fill="url(#g)"/>
        <rect x="10" y="22" width="40" height="16" rx="4" fill="#f8fbff" stroke="#a6aec0"/>
        <g fill="#9ba5b8">
          <rect x="14" y="26" width="4" height="3" rx="1"/>
          <rect x="20" y="26" width="4" height="3" rx="1"/>
          <rect x="26" y="26" width="4" height="3" rx="1"/>
          <rect x="32" y="26" width="4" height="3" rx="1"/>
          <rect x="38" y="26" width="4" height="3" rx="1"/>
          <rect x="14" y="31" width="25" height="3" rx="1"/>
          <rect x="41" y="31" width="5" height="3" rx="1"/>
        </g>
      </svg>`,
    vest: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#1a2436"/>
            <stop offset="1" stop-color="#7e92bf"/>
          </linearGradient>
        </defs>
        <rect width="60" height="60" rx="18" fill="url(#g)"/>
        <path d="M22 16l8 5 8-5 6 10-4 20H20l-4-20 6-10z" fill="#1f2c45"/>
        <path d="M30 21v25" stroke="#6c87c4" stroke-width="2"/>
        <path d="M25 16l5 7 5-7" fill="#8ea2d0"/>
      </svg>`,
  };

  return `url("data:image/svg+xml;utf8,${encodeURIComponent(art[kind])}")`;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function money(value) {
  return `$${value.toFixed(2)}`;
}

function getFilteredProducts() {
  return products.filter((product) => {
    const haystack =
      `${product.name} ${product.sku} ${product.categoryLabel}`.toLowerCase();
    const queryMatch = !state.query || haystack.includes(state.query.toLowerCase());
    const statusMatch = state.status === "all" || product.status === state.status;
    const categoryMatch =
      state.category === "all" || product.category === state.category;

    return queryMatch && statusMatch && categoryMatch;
  });
}

function getPagedProducts(filteredProducts) {
  const totalPages = Math.max(1, Math.ceil(filteredProducts.length / pageSize));
  if (state.page > totalPages) {
    state.page = totalPages;
  }

  const start = (state.page - 1) * pageSize;
  return {
    totalPages,
    start,
    items: filteredProducts.slice(start, start + pageSize),
  };
}

function getPriorityProducts(filteredProducts) {
  return filteredProducts
    .filter((product) => product.status !== "ready")
    .sort((a, b) => a.readiness - b.readiness);
}

function getHealthValue(filteredProducts) {
  if (!filteredProducts.length) {
    return 0;
  }

  const score =
    84 +
    Math.round(
      filteredProducts.filter((product) => product.status === "ready").length /
        filteredProducts.length,
    );
  return Math.min(score, 98);
}

function setScreen(screen) {
  state.screen = screen;
  pageTitle.textContent = screenTitles[screen] || "ShopShot";

  navLinks.forEach((link) => {
    link.classList.toggle("is-active", link.dataset.screen === screen);
  });

  topTabs.forEach((tab) => {
    const active = tab.dataset.screen === screen;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", String(active));
  });

  screens.forEach((panel) => {
    panel.classList.toggle("is-active", panel.dataset.screenPanel === screen);
  });

  updateCopilotShell();
}

function updateCopilotShell() {
  const config = copilotConfig[state.screen] || copilotConfig.catalog;
  copilotStatus.textContent = config.status;
  assistantContext.textContent = config.context;
  actionReviewLabel.textContent = config.actions.review;
  actionOptimizeLabel.textContent = config.actions.optimize;
  actionCategoriesLabel.textContent = config.actions.categories;

  if (state.screen !== "catalog" && config.message) {
    assistantMessage.textContent = config.message;
  }
}

function renderRows(items) {
  if (!items.length) {
    productRows.innerHTML = `
      <div class="empty-state">
        <strong>No products found</strong>
        <span>Try clearing the filters or searching for a different product.</span>
      </div>
    `;
    return;
  }

  productRows.innerHTML = items
    .map((product) => {
      const checked = state.selected.has(product.id) ? "checked" : "";
      const categoryClass =
        product.category === "electronics" ? "is-electronics" : "";
      const lowReadiness = product.readiness < 40 ? "low" : "";
      const scoreClass = product.readiness < 40 ? "low" : "";

      return `
        <div class="table-row table-grid">
          <label class="check-wrap">
            <input
              class="row-checkbox"
              data-id="${product.id}"
              type="checkbox"
              aria-label="Select ${escapeHtml(product.name)}"
              ${checked}
            />
            <span></span>
          </label>

          <div class="product-info">
            <span class="mobile-label">Product</span>
            <div class="product-thumb" style="background-image:${svgThumb(product.thumb)}"></div>
            <div class="product-copy">
              <strong>${escapeHtml(product.name)}</strong>
              <span class="sku">SKU: ${escapeHtml(product.sku)}</span>
            </div>
          </div>

          <div class="table-cell">
            <span class="mobile-label">Category</span>
            <span class="category-badge ${categoryClass}">${escapeHtml(
              product.categoryLabel,
            )}</span>
          </div>

          <div class="table-cell price-cell">
            <span class="mobile-label">Price</span>
            <span class="price">${money(product.price)}</span>
          </div>

          <div class="table-cell">
            <span class="mobile-label">Status</span>
            <span class="status ${product.status}">${escapeHtml(product.statusLabel)}</span>
          </div>

          <div class="table-cell">
            <span class="mobile-label">AI Readiness</span>
            <div class="readiness">
              <div class="readiness-bar">
                <span class="${lowReadiness}" style="width:${product.readiness}%"></span>
              </div>
              <span class="readiness-score ${scoreClass}">${product.readiness}</span>
            </div>
          </div>
        </div>
      `;
    })
    .join("");
}

function renderPagination(totalPages) {
  const previousDisabled = state.page === 1 ? "disabled" : "";
  const nextDisabled = state.page === totalPages ? "disabled" : "";

  const buttons = Array.from({ length: Math.min(totalPages, 3) }, (_, index) => {
    const page = index + 1;
    const active = page === state.page ? "active" : "";
    return `<button class="${active}" data-page="${page}" type="button">${page}</button>`;
  }).join("");

  pagination.innerHTML = `
    <button class="${previousDisabled}" data-page="${state.page - 1}" type="button">‹</button>
    ${buttons}
    <button class="${nextDisabled}" data-page="${state.page + 1}" type="button">›</button>
  `;
}

function syncSelectAll(visibleItems) {
  const selectedCount = visibleItems.filter((item) => state.selected.has(item.id)).length;
  selectAll.checked = visibleItems.length > 0 && selectedCount === visibleItems.length;
  selectAll.indeterminate =
    selectedCount > 0 && selectedCount < visibleItems.length;
}

function updateAssistant(filteredProducts) {
  const priorityProducts = getPriorityProducts(filteredProducts);
  const priorityCount = priorityProducts.length;

  if (!filteredProducts.length) {
    assistantMessage.textContent =
      "No matching products in this view. Clear the filters and I can surface the next best fixes.";
    insightText.textContent =
      "This filtered view is empty, so there are no readiness insights to rank yet.";
    return;
  }

  if (!priorityCount) {
    assistantMessage.textContent =
      "Everything in this view is marked ready. You can export this set or review another category.";
    insightText.textContent =
      "All visible products are in a healthy state. AI recommends exporting or auditing another slice of the catalog next.";
    return;
  }

  const focus = priorityProducts[0];
  assistantMessage.textContent = `Hi! I've analyzed your catalog. You have ${priorityCount} items that need review to reach 100% readiness. Would you like me to start with the "${focus.name}"?`;
  insightText.textContent = `Your overall readiness has improved by 4% since last week. AI recommends updating "${focus.name}" first because it has the biggest impact on catalog quality.`;
}

function renderRecommendations(filteredProducts) {
  const priorityProducts = getPriorityProducts(filteredProducts).slice(0, 3);
  insightPriorityCount.textContent = String(priorityProducts.length);

  if (!priorityProducts.length) {
    insightRecommendations.innerHTML = `
      <div class="recommendation-card">
        <div>
          <strong>All clear</strong>
          <p>Your visible catalog is ready. Export this batch or shift attention to another category.</p>
        </div>
        <span class="tag tag-soft">Ready</span>
      </div>
    `;
    return;
  }

  insightRecommendations.innerHTML = priorityProducts
    .map((product, index) => {
      const label = index === 0 ? "Highest impact" : "Recommended";
      return `
        <div class="recommendation-card">
          <div>
            <strong>${escapeHtml(product.name)}</strong>
            <p>Improve status coverage, refine copy, and fill missing listing fields to lift readiness.</p>
          </div>
          <span class="tag">${label}</span>
        </div>
      `;
    })
    .join("");
}

function renderSummary(filteredProducts, start, visibleCount) {
  if (!filteredProducts.length) {
    resultsSummary.textContent = "Showing 0 products";
    return;
  }

  const from = start + 1;
  const to = start + visibleCount;
  const estimatedTotal = state.query || state.status !== "all" || state.category !== "all"
    ? filteredProducts.length
    : catalogTotal;

  resultsSummary.innerHTML = `Showing <b>${from}-${to}</b> of ${estimatedTotal} products`;
}

function render() {
  const filteredProducts = getFilteredProducts();
  const { totalPages, start, items } = getPagedProducts(filteredProducts);
  const health = getHealthValue(filteredProducts);

  renderRows(items);
  renderPagination(totalPages);
  renderSummary(filteredProducts, start, items.length);
  syncSelectAll(items);
  updateAssistant(filteredProducts);
  renderRecommendations(filteredProducts);

  healthScore.textContent = `${health}%`;
  healthBarFill.style.width = `${health}%`;
}

function updatePreview() {
  const name = listingName.value.trim() || "Untitled product";
  const category = listingCategory.value;
  const channel = listingChannel.value;
  const price = listingPrice.value.trim() || "$0.00";
  const highlights = listingHighlights.value.trim();

  previewTitle.textContent = `${name} for ${category} shoppers`;
  previewDescription.textContent = `${highlights} Optimized for ${channel} with pricing set at ${price}.`;

  const seoScore = Math.min(96, 78 + Math.round(name.length / 2));
  const readiness = Math.min(98, 70 + Math.round(highlights.length / 12));
  const missing = Math.max(0, 4 - Math.floor(highlights.length / 40));

  previewSeo.textContent = String(seoScore);
  previewReadiness.textContent = `${readiness}%`;
  previewMissing.textContent = String(missing);
  createProgressValue.textContent = `${Math.min(96, readiness - 8)}%`;
}

searchInput.addEventListener("input", (event) => {
  state.query = event.target.value.trim();
  state.page = 1;
  render();
});

statusFilter.addEventListener("change", (event) => {
  state.status = event.target.value;
  state.page = 1;
  render();
});

categoryFilter.addEventListener("change", (event) => {
  state.category = event.target.value;
  state.page = 1;
  render();
});

clearFilters.addEventListener("click", () => {
  state.query = "";
  state.status = "all";
  state.category = "all";
  state.page = 1;
  searchInput.value = "";
  statusFilter.value = "all";
  categoryFilter.value = "all";
  render();
});

exportButton.addEventListener("click", () => {
  const count = state.selected.size;
  assistantMessage.textContent = count
    ? `Prepared ${count} selected products for export. I’d review the flagged items before publishing.`
    : "Prepared the current catalog view for export. I’d still review the flagged items before publishing.";
});

navLinks.forEach((link) => {
  link.addEventListener("click", () => {
    setScreen(link.dataset.screen);
  });
});

topTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    setScreen(tab.dataset.screen);
  });
});

openCreateButton.addEventListener("click", () => {
  setScreen("create");
});

productRows.addEventListener("change", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLInputElement) || !target.classList.contains("row-checkbox")) {
    return;
  }

  const id = Number(target.dataset.id);
  if (target.checked) {
    state.selected.add(id);
  } else {
    state.selected.delete(id);
  }

  render();
});

selectAll.addEventListener("change", () => {
  const visibleItems = getPagedProducts(getFilteredProducts()).items;

  visibleItems.forEach((item) => {
    if (selectAll.checked) {
      state.selected.add(item.id);
    } else {
      state.selected.delete(item.id);
    }
  });

  render();
});

pagination.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof Element)) {
    return;
  }

  const button = target.closest("button");
  if (!button || button.classList.contains("disabled")) {
    return;
  }

  const nextPage = Number(button.dataset.page);
  if (!Number.isNaN(nextPage) && nextPage > 0) {
    state.page = nextPage;
    render();
  }
});

quickActions.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof Element)) {
    return;
  }

  const button = target.closest("[data-action]");
  if (!button) {
    return;
  }

  const filteredProducts = getFilteredProducts();
  const priorities = getPriorityProducts(filteredProducts);

  if (state.screen === "insights") {
    if (button.dataset.action === "review") {
      assistantMessage.textContent =
        "I’d start with a short cleanup sprint: draft fixes first, then low-readiness review items, then taxonomy cleanup.";
    }

    if (button.dataset.action === "optimize") {
      assistantMessage.textContent =
        "The weekly lift is coming from more products reaching ready status, not from one single category spike.";
    }

    if (button.dataset.action === "categories") {
      assistantMessage.textContent =
        "The biggest risk area is still low-readiness inventory inside Electronics and Home.";
    }
    return;
  }

  if (state.screen === "create") {
    if (button.dataset.action === "review") {
      assistantMessage.textContent =
        "The draft is strongest when the title is sharper, the first line explains the use case, and the missing fields are resolved.";
    }

    if (button.dataset.action === "optimize") {
      assistantMessage.textContent =
        "Suggested title rewrite: keep the product name first, add a buyer benefit second, and avoid extra filler words.";
    }

    if (button.dataset.action === "categories") {
      assistantMessage.textContent =
        "Before publish, confirm materials, dimensions, and shipping attributes to avoid a readiness penalty.";
    }
    return;
  }

  if (state.screen === "settings") {
    if (button.dataset.action === "review") {
      assistantMessage.textContent =
        "Recommended defaults: keep descriptions and alerts on, and only enable auto-export once the review workflow is stable.";
    }

    if (button.dataset.action === "optimize") {
      assistantMessage.textContent =
        "The easiest way to reduce manual work is to keep AI draft generation on while leaving export approval in human hands.";
    }

    if (button.dataset.action === "categories") {
      assistantMessage.textContent =
        "Channel setup looks healthiest when connected stores are current and export rules match the right catalog category tree.";
    }
    return;
  }

  if (state.screen === "support") {
    if (button.dataset.action === "review") {
      assistantMessage.textContent =
        "For export issues, first check channel auth, then missing required fields, then any readiness blockers preventing publish.";
    }

    if (button.dataset.action === "optimize") {
      assistantMessage.textContent =
        "Content quality improves fastest when titles match search intent and descriptions answer materials, size, and use case clearly.";
    }

    if (button.dataset.action === "categories") {
      assistantMessage.textContent =
        "Catalog issues usually come from duplicate SKUs, weak category mapping, or products stuck in draft too long.";
    }
    return;
  }

  if (button.dataset.action === "review") {
    assistantMessage.textContent = priorities.length
      ? `I prioritized the review queue. Start with "${priorities[0].name}" and then move through the remaining flagged products.`
      : "Nothing in the current view needs review right now.";
  }

  if (button.dataset.action === "optimize") {
    assistantMessage.textContent =
      "Description optimization is queued. I’d tighten benefit-led first lines and fill in missing material details next.";
  }

  if (button.dataset.action === "categories") {
    assistantMessage.textContent =
      "Category audit complete. The biggest taxonomy cleanup opportunities are in Electronics and Home.";
  }
});

listingForm.addEventListener("submit", (event) => {
  event.preventDefault();
  updatePreview();
  assistantMessage.textContent =
    "Draft regenerated. I tightened the title, refreshed the description, and updated the missing-field count for review.";
});

[listingName, listingCategory, listingChannel, listingPrice, listingHighlights].forEach(
  (field) => {
    field.addEventListener("input", updatePreview);
    field.addEventListener("change", updatePreview);
  },
);

settingsToggles.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof Element)) {
    return;
  }

  const button = target.closest("[data-setting]");
  if (!button) {
    return;
  }

  const key = button.dataset.setting;
  state.settings[key] = !state.settings[key];
  button.classList.toggle("is-on", state.settings[key]);
  assistantMessage.textContent = `${button.querySelector("strong").textContent} ${
    state.settings[key] ? "enabled" : "disabled"
  }.`;
});

document.querySelectorAll(".support-tile").forEach((button) => {
  button.addEventListener("click", () => {
    const helpMessages = {
      export:
        "Export issues usually come from channel auth or missing required fields. Start by reconnecting the channel and reviewing flagged drafts.",
      content:
        "Content quality improves fastest when you rewrite titles for intent, then fill materials, dimensions, and benefit-led opening lines.",
      catalog:
        "Catalog cleanup should start with low-readiness items, duplicate SKUs, and products sitting in the wrong category tree.",
    };

    supportResponse.textContent = helpMessages[button.dataset.help];
  });
});

assistantForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const value = assistantPrompt.value.trim();
  if (!value) {
    return;
  }

  assistantMessage.textContent = `AI Copilot: "${value}" is queued. I’d begin with low-readiness products, then refine titles, descriptions, and category mapping.`;
  assistantPrompt.value = "";
});

updatePreview();
setScreen("catalog");
render();
