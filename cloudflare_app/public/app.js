const [predictionsResponse, scheduleResponse, registryResponse] = await Promise.all([
  fetch("/data/predictions.json"),
  fetch("/data/schedule_2026.json"),
  fetch("/data/model_registry.json"),
]);

if (!predictionsResponse.ok) throw new Error("Could not load predictions.json");
if (!scheduleResponse.ok) throw new Error("Could not load schedule_2026.json");
if (!registryResponse.ok) throw new Error("Could not load model_registry.json");

const predictionStore = await predictionsResponse.json();
const schedule = await scheduleResponse.json();
const modelRegistry = await registryResponse.json();
const allPredictions = predictionStore.predictions || [];
const modelRows = Object.entries(modelRegistry.models || {}).map(([alias, metadata], index) => ({
  alias,
  index,
  ...(typeof metadata === "string" ? { model: metadata } : metadata),
}));
const modelMetadata = new Map(modelRows.map((row) => [row.alias, row]));

renderSchedule();
selectMatch(matchIdFromHash() || 1);
wireTabs();

window.addEventListener("hashchange", () => {
  selectMatch(matchIdFromHash() || 1);
});

function renderSchedule() {
  const list = document.getElementById("scheduleList");
  const chronologicalSchedule = [...schedule].sort((a, b) => {
    const kickoffA = Date.parse(a.kickoff_utc || `${a.date}T23:59:59Z`);
    const kickoffB = Date.parse(b.kickoff_utc || `${b.date}T23:59:59Z`);
    return kickoffA - kickoffB || Number(a.match_id) - Number(b.match_id);
  });
  const buttons = chronologicalSchedule.map((match) => {
    const button = document.createElement("button");
    button.className = "schedule-item";
    button.type = "button";
    button.dataset.matchId = match.match_id;
    button.innerHTML = `
      <span class="schedule-num">${String(match.match_id).padStart(3, "0")}</span>
      <span class="schedule-teams">${escapeHtml(match.team1)} <b>vs</b> ${escapeHtml(match.team2)}</span>
      <span class="schedule-meta">${escapeHtml(match.date)} · ${escapeHtml(match.ground)}</span>
    `;
    button.addEventListener("click", () => {
      window.location.hash = `match-${match.match_id}`;
    });
    return button;
  });
  list.replaceChildren(...buttons);
}

function selectMatch(matchId) {
  const match = schedule.find((item) => Number(item.match_id) === Number(matchId)) || schedule[0];
  const matchName = `${match.team1} vs ${match.team2}`;
  const predictions = latestByAlias(
    allPredictions.filter((row) => Number(row.match_id) === Number(match.match_id) || row.match === matchName),
  );

  for (const button of document.querySelectorAll(".schedule-item")) {
    button.classList.toggle("active", Number(button.dataset.matchId) === Number(match.match_id));
  }

  renderSummary(match, predictions);
  renderPredictionState(predictions);
  renderPredictionTable(predictions);
}

function latestByAlias(rows) {
  const byAlias = new Map();
  for (const row of rows) {
    const alias = aliasForRow(row);
    byAlias.set(alias, row);
  }
  return Array.from(byAlias.values()).sort((a, b) => modelSortIndex(a) - modelSortIndex(b));
}

function renderSummary(match, rows) {
  const matchName = `${match.team1} vs ${match.team2}`;
  const consensus = mode(rows.map((row) => row.prediction));
  const scoreConsensus = mode(rows.map((row) => row.scoreline));
  const totalTokens = rows.reduce((sum, row) => sum + Number(row.usage?.totals?.total_tokens || 0), 0);
  const totalCost = rows.reduce((sum, row) => sum + Number(row.usage?.totals?.cost || 0), 0);

  document.getElementById("matchName").textContent = `${matchName} · ${match.date} · ${match.ground}`;
  document.getElementById("consensus").textContent = consensus ? `${consensus} consensus` : "No predictions yet";
  document.getElementById("modelCount").textContent = rows.length;
  document.getElementById("tokenTotal").textContent = rows.length ? formatInteger(totalTokens) : "-";
  document.getElementById("costTotal").textContent = rows.length ? formatCurrency(totalCost) : "-";
  document.getElementById("scoreConsensus").textContent = scoreConsensus || "-";
}

function renderPredictionState(rows) {
  const tbaView = document.getElementById("tbaView");
  const predictionContent = document.getElementById("predictionContent");
  tbaView.hidden = rows.length > 0;
  predictionContent.hidden = rows.length === 0;
}

function renderPredictionTable(rows) {
  const body = document.getElementById("predictionRows");
  if (!rows.length) {
    body.replaceChildren();
    return;
  }

  const tableRows = rows.map((row, index) => {
      const tr = document.createElement("tr");
      tr.className = "prediction-row";
      tr.tabIndex = 0;
      tr.dataset.modelAlias = row.model_alias || row.model;
      tr.append(
        modelCell(row),
        cellWithPick(row.prediction),
        cell(row.scoreline),
        cell(formatPercent(row.confidence)),
        cell(formatCurrency(row.usage?.totals?.cost || 0)),
      );
      tr.addEventListener("click", () => selectPredictionRow(tr, row));
      tr.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectPredictionRow(tr, row);
        }
      });
      if (index === 0) {
        queueMicrotask(() => selectPredictionRow(tr, row));
      }
      return tr;
    });
  body.replaceChildren(...tableRows);
}

function selectPredictionRow(rowElement, prediction) {
  const wasSelected = rowElement.classList.contains("selected");
  document.querySelector(".prediction-detail-row")?.remove();
  if (wasSelected) {
    rowElement.classList.remove("selected");
    return;
  }

  for (const row of document.querySelectorAll(".prediction-row")) {
    row.classList.toggle("selected", row === rowElement);
  }
  rowElement.insertAdjacentElement("afterend", createPredictionDetailRow(prediction));
}

function createPredictionDetailRow(row) {
  const tr = document.createElement("tr");
  tr.className = "prediction-detail-row";
  const td = document.createElement("td");
  td.colSpan = 5;
  td.innerHTML = `
    <div class="inline-detail">
      <p>${escapeHtml(row.rationale || "No rationale saved.")}</p>
      <dl>
        <dt>Players to watch</dt>
        <dd>${escapeHtml(row.players_to_watch || "-")}</dd>
        <dt>Usage</dt>
        <dd>${formatInteger(row.usage?.totals?.total_tokens || 0)} tokens · ${formatCurrency(row.usage?.totals?.cost || 0)}</dd>
      </dl>
    </div>
  `;
  tr.append(td);
  return tr;
}

function modelSortIndex(row) {
  const alias = aliasForRow(row);
  return modelMetadata.get(alias)?.index ?? 9999;
}

function metadataFor(row) {
  return modelMetadata.get(aliasForRow(row)) || {};
}

function modelCell(row) {
  const td = document.createElement("td");
  const metadata = metadataFor(row);
  td.innerHTML = `
    <span class="model-label">
        ${providerIcon(metadata)}
      <span>
        <strong>${escapeHtml(aliasForRow(row))}</strong>
        <small>${escapeHtml(metadata.group || metadata.provider_label || "")}</small>
      </span>
    </span>
  `;
  return td;
}

function aliasForRow(row) {
  if (row.model_alias) return row.model_alias;
  const match = modelRows.find((model) => model.model === row.model);
  return match?.alias || row.model || "unknown";
}

function providerIcon(metadata) {
  if (!metadata?.icon) return '<span class="provider-fallback">?</span>';
  return `<img class="provider-icon" src="${escapeHtml(metadata.icon)}" alt="${escapeHtml(metadata.provider_label || "Provider")}">`;
}

function wireTabs() {
  const predictionsTab = document.getElementById("predictionsTab");
  const leaderboardTab = document.getElementById("leaderboardTab");
  const predictionsView = document.getElementById("predictionsView");
  const modelLeaderboardView = document.getElementById("modelLeaderboardView");

  predictionsTab.addEventListener("click", () => {
    predictionsTab.classList.add("active");
    leaderboardTab.classList.remove("active");
    predictionsView.hidden = false;
    modelLeaderboardView.hidden = true;
  });

  leaderboardTab.addEventListener("click", () => {
    leaderboardTab.classList.add("active");
    predictionsTab.classList.remove("active");
    predictionsView.hidden = true;
    modelLeaderboardView.hidden = false;
  });
}

function matchIdFromHash() {
  const match = window.location.hash.match(/^#match-(\d+)$/);
  return match ? Number(match[1]) : null;
}

function mode(values) {
  const counts = new Map();
  for (const value of values.filter(Boolean)) {
    counts.set(value, (counts.get(value) || 0) + 1);
  }
  return Array.from(counts.entries()).sort((a, b) => b[1] - a[1])[0]?.[0] || "";
}

function cell(value) {
  const td = document.createElement("td");
  td.textContent = value ?? "";
  return td;
}

function cellWithPick(value) {
  const td = document.createElement("td");
  const span = document.createElement("span");
  span.className = "pick";
  span.textContent = value ?? "";
  td.append(span);
  return td;
}

function formatInteger(value) {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatCurrency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 4,
  }).format(value);
}

function formatPercent(value) {
  if (value === undefined || value === null || value === "") return "";
  return `${Math.round(Number(value) * 100)}%`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
