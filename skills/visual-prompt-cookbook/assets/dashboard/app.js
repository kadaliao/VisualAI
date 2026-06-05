let styles = [];

const grid = document.querySelector("#grid");
const detail = document.querySelector("#detail");
const search = document.querySelector("#search");
const meta = document.querySelector("#meta");

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
    ...(style.tags || []),
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
    <h2>${escapeHtml(style.style_name)}</h2>
    <p>${escapeHtml(style.style_summary)}</p>
    <small>${escapeHtml((style.tags || []).join(" / "))}</small>
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
  const response = await fetch(`/api/style/${encodeURIComponent(style.style_slug)}`);
  const data = await response.json();
  await fetch("/api/select", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ id: style.id, style_slug: style.style_slug, style_name: style.style_name }),
  });
  detail.innerHTML = `
    <img class="hero" src="/cookbook/${escapeHtml(style.preview_9x16)}" alt="">
    <h2>#${escapeHtml(style.id)} ${escapeHtml(style.style_name)}</h2>
    <p>${escapeHtml(style.style_summary)}</p>
    <h3>Variables</h3>
    <dl>
      ${Object.entries(data.environment_variables || {}).map(([name, desc]) => `<dt>${escapeHtml(name)}</dt><dd>${escapeHtml(desc)}</dd>`).join("")}
    </dl>
    <p class="muted">Reply in Codex with #${escapeHtml(style.id)} or ${escapeHtml(style.style_slug)} to continue.</p>
  `;
}

async function init() {
  const response = await fetch("/api/index");
  const index = await response.json();
  styles = index.styles || [];
  meta.textContent = `${index.style_count || styles.length} styles · upstream ${index.upstream?.commit_sha || "unknown"}`;
  renderGrid();
}

search.addEventListener("input", renderGrid);
init().catch((error) => {
  meta.textContent = `Failed to load styles: ${error}`;
});
