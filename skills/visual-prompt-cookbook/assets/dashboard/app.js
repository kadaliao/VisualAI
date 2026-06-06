let styles = [];
let uiLanguage = "en";

const I18N = {
  en: {
    appTitle: "Visual Prompt Cookbook",
    detailLabel: "Style detail",
    emptyDetail: "Select a style to inspect variables and examples.",
    failedToLoad: "Failed to load styles",
    galleryLabel: "Style gallery",
    loading: "Loading styles...",
    replyHint: (style) => `Reply in your agent with #${style.id} or ${style.style_slug} to continue.`,
    searchPlaceholder: "Search styles, tags, or slug",
    styles: "styles",
    upstream: "upstream",
    variables: "Variables",
  },
  "zh-CN": {
    appTitle: "视觉提示词风格库",
    detailLabel: "风格详情",
    emptyDetail: "选择一个风格，查看变量和示例。",
    failedToLoad: "风格加载失败",
    galleryLabel: "风格画廊",
    loading: "正在加载风格...",
    replyHint: (style) => `在当前 agent 中回复 #${style.id} 或 ${style.style_slug} 继续。`,
    searchPlaceholder: "搜索风格、标签或 slug",
    styles: "个风格",
    upstream: "上游",
    variables: "变量",
  },
};

const grid = document.querySelector("#grid");
const detail = document.querySelector("#detail");
const search = document.querySelector("#search");
const meta = document.querySelector("#meta");

function requestedLanguage(configLanguage) {
  const value = configLanguage || "auto";
  if (value !== "auto") {
    return value;
  }
  const browserLanguage = navigator.language || "";
  return browserLanguage.toLowerCase().startsWith("zh") ? "zh-CN" : "en";
}

function t(key) {
  return I18N[uiLanguage][key];
}

function languageQuery() {
  return `language=${encodeURIComponent(uiLanguage)}`;
}

function displayName(style) {
  return style.display?.name || style.style_name;
}

function displaySummary(style) {
  return style.display?.summary || style.style_summary;
}

function displayTags(style) {
  return style.display?.tags || style.tags || [];
}

function applyLanguage(language) {
  uiLanguage = I18N[language] ? language : "en";
  document.documentElement.lang = uiLanguage === "zh-CN" ? "zh-CN" : "en";
  document.title = t("appTitle");
  document.querySelector("h1").textContent = t("appTitle");
  search.placeholder = t("searchPlaceholder");
  grid.setAttribute("aria-label", t("galleryLabel"));
  detail.setAttribute("aria-label", t("detailLabel"));
  const emptyDetail = document.querySelector("#empty-detail");
  if (emptyDetail) {
    emptyDetail.textContent = t("emptyDetail");
  }
  meta.textContent = t("loading");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function matchStyle(style, query) {
  const haystack = [
    style.id,
    style.style_name,
    style.style_slug,
    style.style_summary,
    style.display?.name,
    style.display?.summary,
    ...(style.tags || []),
    ...(style.display?.tags || []),
  ].join(" ").toLowerCase();
  return haystack.includes(query.toLowerCase());
}

function card(style) {
  const node = document.createElement("button");
  node.className = "card";
  node.type = "button";
  node.innerHTML = `
    <img src="/cookbook/${escapeHtml(style.preview_16x9)}" alt="">
    <span class="id">#${escapeHtml(style.id)}</span>
    <h2>${escapeHtml(displayName(style))}</h2>
    <p>${escapeHtml(displaySummary(style))}</p>
    <small>${escapeHtml(displayTags(style).join(" / "))}</small>
  `;
  node.addEventListener("click", () => selectStyle(style));
  return node;
}

function renderGrid() {
  const query = search.value.trim();
  grid.innerHTML = "";
  styles.filter((style) => !query || matchStyle(style, query)).forEach((style) => grid.appendChild(card(style)));
}

async function selectStyle(style) {
  const response = await fetch(`/api/style/${encodeURIComponent(style.style_slug)}?${languageQuery()}`);
  const data = await response.json();
  await fetch("/api/select", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      id: style.id,
      style_slug: style.style_slug,
      style_name: style.style_name,
      display_name: displayName(style),
      language: uiLanguage,
    }),
  });
  const variableDisplay = data.display?.environment_variables || {};
  detail.innerHTML = `
    <img class="hero" src="/cookbook/${escapeHtml(style.preview_9x16)}" alt="">
    <h2>#${escapeHtml(style.id)} ${escapeHtml(data.display?.name || displayName(style))}</h2>
    <p>${escapeHtml(data.display?.summary || displaySummary(style))}</p>
    <h3>${escapeHtml(t("variables"))}</h3>
    <dl>
      ${Object.entries(data.environment_variables || {}).map(([name, desc]) => {
        const localized = variableDisplay[name] || {};
        const label = localized.label ? `${localized.label} (${name})` : name;
        return `<dt>${escapeHtml(label)}</dt><dd>${escapeHtml(localized.description || desc)}</dd>`;
      }).join("")}
    </dl>
    <p class="muted">${escapeHtml(t("replyHint")(style))}</p>
  `;
}

async function init() {
  const configResponse = await fetch("/api/config");
  const config = await configResponse.json();
  applyLanguage(requestedLanguage(config.language));
  const indexResponse = await fetch(`/api/index?${languageQuery()}`);
  const index = await indexResponse.json();
  styles = index.styles || [];
  meta.textContent = `${index.style_count || styles.length} ${t("styles")} · ${t("upstream")} ${index.upstream?.commit_sha || "unknown"}`;
  renderGrid();
}

search.addEventListener("input", renderGrid);
init().catch((error) => {
  meta.textContent = `${t("failedToLoad")}: ${error}`;
});
