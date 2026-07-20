const [predictionsResponse, scheduleResponse, registryResponse] = await Promise.all([
  fetch("/data/predictions.json", { cache: "no-store" }),
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
const leaderboardSort = { key: "total_points", direction: "desc" };
const pickColors = {
  Algeria: { bg: "#006633", fg: "#ffffff" },
  Argentina: { bg: "#75aadb", fg: "#14110f" },
  Australia: { bg: "#ffcd00", fg: "#14110f" },
  Austria: { bg: "#c8102e", fg: "#ffffff" },
  Belgium: { bg: "#fae042", fg: "#14110f" },
  "Bosnia & Herzegovina": { bg: "#002f6c", fg: "#ffffff" },
  Brazil: { bg: "#009b3a", fg: "#ffffff" },
  Canada: { bg: "#d80621", fg: "#ffffff" },
  "Cape Verde": { bg: "#003893", fg: "#ffffff" },
  Colombia: { bg: "#fcd116", fg: "#14110f" },
  Croatia: { bg: "#171796", fg: "#ffffff" },
  "Curaçao": { bg: "#002b7f", fg: "#ffffff" },
  "Czech Republic": { bg: "#d7141a", fg: "#ffffff" },
  "DR Congo": { bg: "#007fff", fg: "#14110f" },
  Ecuador: { bg: "#ffdd00", fg: "#14110f" },
  Egypt: { bg: "#ce1126", fg: "#ffffff" },
  England: { bg: "#cf142b", fg: "#ffffff" },
  France: { bg: "#0055a4", fg: "#ffffff" },
  Germany: { bg: "#000000", fg: "#ffffff" },
  Ghana: { bg: "#fcd116", fg: "#14110f" },
  Haiti: { bg: "#00209f", fg: "#ffffff" },
  Iran: { bg: "#239f40", fg: "#ffffff" },
  Iraq: { bg: "#ce1126", fg: "#ffffff" },
  "Ivory Coast": { bg: "#f77f00", fg: "#14110f" },
  Japan: { bg: "#bc002d", fg: "#ffffff" },
  Jordan: { bg: "#007a3d", fg: "#ffffff" },
  Mexico: { bg: "#006847", fg: "#ffffff" },
  Morocco: { bg: "#c1272d", fg: "#ffffff" },
  Netherlands: { bg: "#ff4f00", fg: "#14110f" },
  "New Zealand": { bg: "#00247d", fg: "#ffffff" },
  Norway: { bg: "#ba0c2f", fg: "#ffffff" },
  Panama: { bg: "#005293", fg: "#ffffff" },
  Paraguay: { bg: "#0038a8", fg: "#ffffff" },
  Portugal: { bg: "#006600", fg: "#ffffff" },
  Qatar: { bg: "#8a1538", fg: "#ffffff" },
  "Saudi Arabia": { bg: "#006c35", fg: "#ffffff" },
  Scotland: { bg: "#005eb8", fg: "#ffffff" },
  Senegal: { bg: "#00853f", fg: "#ffffff" },
  "South Africa": { bg: "#007a4d", fg: "#ffffff" },
  "South Korea": { bg: "#c60c30", fg: "#ffffff" },
  Spain: { bg: "#aa151b", fg: "#ffffff" },
  Sweden: { bg: "#006aa7", fg: "#ffffff" },
  Switzerland: { bg: "#d52b1e", fg: "#ffffff" },
  Tunisia: { bg: "#e70013", fg: "#ffffff" },
  Turkey: { bg: "#e30a17", fg: "#ffffff" },
  "United States": { bg: "#3c3b6e", fg: "#ffffff" },
  Uruguay: { bg: "#0038a8", fg: "#ffffff" },
  Uzbekistan: { bg: "#0099b5", fg: "#14110f" },
  Draw: { bg: "#b8b1a7", fg: "#14110f" },
};

renderSchedule();
renderLeaderboard();
selectMatch(selectableMatchId(matchIdFromHash()) || defaultMatchId());
wireTabs();
wireDownload();

window.addEventListener("hashchange", () => {
  selectMatch(selectableMatchId(matchIdFromHash()) || defaultMatchId());
});

function renderSchedule() {
  const list = document.getElementById("scheduleList");
  const chronologicalSchedule = chronologicalMatches();
  const buttons = chronologicalSchedule.map((match, index) => {
    const status = matchStatus(match);
    const button = document.createElement("button");
    button.className = `schedule-item ${status}`;
    button.type = "button";
    button.dataset.matchId = match.match_id;
    button.disabled = status === "upcoming";
    button.setAttribute("aria-label", `${match.team1} vs ${match.team2}, ${status}`);
    button.innerHTML = `
      <span class="schedule-num">${String(index + 1).padStart(3, "0")}</span>
      <span class="schedule-teams">${escapeHtml(match.team1)} <b>vs</b> ${escapeHtml(match.team2)}</span>
      <span class="schedule-meta">${escapeHtml(match.date)} · ${escapeHtml(match.ground)}</span>
      <span class="schedule-status" aria-hidden="true"></span>
    `;
    button.addEventListener("click", () => {
      window.location.hash = `match-${index + 1}`;
    });
    return button;
  });
  list.replaceChildren(...buttons);
}

function selectMatch(matchId) {
  const match = schedule.find((item) => Number(item.match_id) === Number(matchId)) || schedule[0];
  const predictions = latestByAlias(predictionsForMatch(match));
  const result = predictionStore.results?.[String(match.match_id)];

  for (const button of document.querySelectorAll(".schedule-item")) {
    button.classList.toggle("active", Number(button.dataset.matchId) === Number(match.match_id));
  }
  document.querySelector(".schedule-item.active")?.scrollIntoView({ block: "nearest" });

  renderSummary(match, predictions, result);
  renderPredictionState(predictions);
  renderTugOfWar(match, predictions, result);
  renderPredictionTable(predictions);
}

function matchStatus(match) {
  const predictions = predictionsForMatch(match);
  if (predictionStore.results?.[String(match.match_id)] || predictions.some((row) => row.score)) {
    return "done";
  }
  return predictions.length ? "predicted" : "upcoming";
}

function predictionsForMatch(match) {
  const matchName = `${match.team1} vs ${match.team2}`;
  return allPredictions.filter(
    (row) => Number(row.match_id) === Number(match.match_id) || row.match === matchName,
  );
}

function defaultMatchId() {
  const chronologicalSchedule = chronologicalMatches();
  const firstPredicted = chronologicalSchedule.find((match) => matchStatus(match) === "predicted");
  if (firstPredicted) return Number(firstPredicted.match_id);

  const doneMatches = chronologicalSchedule.filter((match) => matchStatus(match) === "done");
  return Number(doneMatches.at(-1)?.match_id || chronologicalSchedule[0]?.match_id || 1);
}

function selectableMatchId(matchId) {
  if (!matchId) return null;
  const match = schedule.find((item) => Number(item.match_id) === Number(matchId));
  return match && matchStatus(match) !== "upcoming" ? Number(match.match_id) : null;
}

function chronologicalMatches() {
  return [...schedule].sort((a, b) => {
    const kickoffA = Date.parse(a.kickoff_utc || `${a.date}T23:59:59Z`);
    const kickoffB = Date.parse(b.kickoff_utc || `${b.date}T23:59:59Z`);
    return kickoffA - kickoffB || Number(a.match_id) - Number(b.match_id);
  });
}

function latestByAlias(rows) {
  const byAlias = new Map();
  for (const row of rows) {
    const alias = aliasForRow(row);
    if (!modelMetadata.has(alias)) continue;
    byAlias.set(alias, row);
  }
  return Array.from(byAlias.values()).sort((a, b) => modelSortIndex(a) - modelSortIndex(b));
}

function renderSummary(match, rows, result) {
  const matchName = `${match.team1} vs ${match.team2}`;
  const consensus = mode(rows.map((row) => row.prediction));
  const scoreConsensus = mode(rows.map((row) => row.scoreline));
  const totalTokens = rows.reduce((sum, row) => sum + Number(row.usage?.totals?.total_tokens || 0), 0);
  const totalCost = rows.reduce((sum, row) => sum + Number(row.usage?.totals?.cost || 0), 0);

  document.getElementById("matchName").textContent = `${matchName} · ${match.date} · ${match.ground}`;
  document.getElementById("consensus").textContent = result
    ? `Final: ${result.team1} ${result.team1_score}-${result.team2_score} ${result.team2}`
    : consensus
      ? `${consensus} consensus`
      : "No predictions yet";
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

function renderTugOfWar(match, rows, result) {
  const element = document.getElementById("tugOfWar");
  if (!rows.length) {
    element.replaceChildren();
    return;
  }

  const team1 = match.team1;
  const team2 = match.team2;
  const pull = weightedPull(team1, team2, rows);
  const team1Colors = pickColors[team1] || pickColors.Draw;
  const team2Colors = pickColors[team2] || pickColors.Draw;
  const leader = pull.team1 === pull.team2
    ? "Even pull"
    : `${pull.team1 > pull.team2 ? team1 : team2} ${Math.abs(pull.team1 - pull.team2)} pts ahead`;
  const finalLine = result
    ? `Final ${result.team1} ${result.team1_score}-${result.team2_score} ${result.team2}`
    : "";

  element.style.setProperty("--team1-bg", team1Colors.bg);
  element.style.setProperty("--team1-fg", team1Colors.fg);
  element.style.setProperty("--team2-bg", team2Colors.bg);
  element.style.setProperty("--team2-fg", team2Colors.fg);
  element.style.setProperty("--team1-pull", `${pull.team1}%`);
  element.innerHTML = `
    <div class="tug-head">
      <div>
        <p class="eyebrow">Model pull</p>
        <strong>${escapeHtml(leader)}</strong>
      </div>
      ${finalLine ? `<span class="tug-final">${escapeHtml(finalLine)}</span>` : ""}
    </div>
    <div class="tug-stage">
      <div class="tug-team tug-team-one">
        <span>${escapeHtml(team1)}</span>
        <strong>${pull.team1}%</strong>
      </div>
      <div class="tug-rope" aria-hidden="true">
        <span class="tug-left"></span>
        <span class="tug-knot"></span>
        <span class="tug-right"></span>
      </div>
      <div class="tug-team tug-team-two">
        <strong>${pull.team2}%</strong>
        <span>${escapeHtml(team2)}</span>
      </div>
    </div>
  `;
}

function weightedPull(team1, team2, rows) {
  let team1Pull = 0;
  let team2Pull = 0;

  for (const row of rows) {
    const confidence = confidenceWeight(row.confidence);
    if (row.prediction === team1) {
      team1Pull += 0.5 + confidence / 2;
      team2Pull += 0.5 - confidence / 2;
    } else if (row.prediction === team2) {
      team1Pull += 0.5 - confidence / 2;
      team2Pull += 0.5 + confidence / 2;
    } else if (row.prediction === "Draw") {
      team1Pull += 0.5;
      team2Pull += 0.5;
    }
  }

  const total = team1Pull + team2Pull;
  if (!total) return { team1: 50, team2: 50 };

  const team1Percent = Math.round((team1Pull / total) * 100);
  return { team1: team1Percent, team2: 100 - team1Percent };
}

function confidenceWeight(value) {
  if (value === undefined || value === null || value === "") return 1;
  return Math.min(Math.max(Number(value), 0), 1);
}

function renderPredictionTable(rows) {
  const body = document.getElementById("predictionRows");
  if (!rows.length) {
    body.replaceChildren();
    return;
  }

  const tableRows = rows.map((row) => {
      const tr = document.createElement("tr");
      tr.className = "prediction-row";
      tr.tabIndex = 0;
      tr.dataset.modelAlias = row.model_alias || row.model;
      tr.append(
        modelCell(row),
        cellWithPick(row.prediction),
        cell(row.scoreline),
        cell(formatPercent(row.confidence)),
        cellWithScore(row.score),
        cell(formatCurrency(row.usage?.totals?.cost || 0)),
      );
      tr.addEventListener("click", () => selectPredictionRow(tr, row));
      tr.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectPredictionRow(tr, row);
        }
      });
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
  td.colSpan = 6;
  td.innerHTML = `
    <div class="inline-detail">
      <section class="reasoning-column">
        <span class="detail-label">Reasoning</span>
        <p>${escapeHtml(row.rationale || "No rationale saved.")}</p>
        <dl>
          <dt>Goal scorers</dt>
          <dd>${escapeHtml(formatGoalScorers(row.goal_scorers))}</dd>
          <dt>Usage</dt>
          <dd>${formatInteger(row.usage?.totals?.total_tokens || 0)} tokens · ${formatCurrency(row.usage?.totals?.cost || 0)}</dd>
        </dl>
      </section>
      <section class="score-column">
        ${scoreBreakdownHtml(row.score)}
      </section>
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
        <small>${escapeHtml(metadata.provider_label || metadata.group || "")}</small>
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

function renderLeaderboard() {
  const leaderboard = predictionStore.leaderboard;
  const unavailable = document.getElementById("leaderboardUnavailable");
  const content = document.getElementById("leaderboardContent");
  if (!leaderboard?.available) {
    unavailable.hidden = false;
    content.hidden = true;
    return;
  }

  unavailable.hidden = true;
  content.hidden = false;
  const rankedRows = leaderboard.rows.map((row, index) => ({ ...row, rank: index + 1 }));
  const sortedRows = rankedRows.sort((a, b) => compareLeaderboardRows(a, b));
  const rows = sortedRows.map((row) => {
    const tr = document.createElement("tr");
    tr.className = "leaderboard-row";
    tr.tabIndex = 0;
    tr.dataset.modelAlias = row.model_alias;
    tr.append(
      cell(row.rank),
      modelCell(row),
      cell(row.total_points),
      cell(`${Number(row.average_points).toFixed(1)}/100`),
      cell(row.matches_scored),
      cell(row.correct_results),
      cell(row.exact_scores),
      cell(formatCurrency(row.total_cost || 0)),
    );
    tr.addEventListener("click", () => selectLeaderboardRow(tr, row));
    tr.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectLeaderboardRow(tr, row);
      }
    });
    return tr;
  });
  document.getElementById("leaderboardRows").replaceChildren(...rows);
  wireLeaderboardSort();
}

function compareLeaderboardRows(a, b) {
  const aValue = a[leaderboardSort.key];
  const bValue = b[leaderboardSort.key];
  const comparison = typeof aValue === "string"
    ? aValue.localeCompare(bValue)
    : Number(aValue) - Number(bValue);
  if (comparison) return leaderboardSort.direction === "asc" ? comparison : -comparison;
  return a.rank - b.rank;
}

function wireLeaderboardSort() {
  for (const button of document.querySelectorAll(".sort-button")) {
    const active = button.dataset.sort === leaderboardSort.key;
    button.classList.toggle("active", active);
    button.setAttribute("aria-sort", active
      ? (leaderboardSort.direction === "asc" ? "ascending" : "descending")
      : "none");
    button.querySelector("b").textContent = active
      ? (leaderboardSort.direction === "asc" ? "↑" : "↓")
      : "";
    button.onclick = () => {
      if (leaderboardSort.key === button.dataset.sort) {
        leaderboardSort.direction = leaderboardSort.direction === "asc" ? "desc" : "asc";
      } else {
        leaderboardSort.key = button.dataset.sort;
        leaderboardSort.direction = button.dataset.sort === "model_alias" ? "asc" : "desc";
      }
      renderLeaderboard();
    };
  }
}

function selectLeaderboardRow(rowElement, leaderboardRow) {
  const wasSelected = rowElement.classList.contains("selected");
  document.querySelector(".leaderboard-detail-row")?.remove();
  for (const row of document.querySelectorAll(".leaderboard-row")) {
    row.classList.remove("selected");
  }
  if (wasSelected) return;

  rowElement.classList.add("selected");
  rowElement.insertAdjacentElement("afterend", createLeaderboardDetailRow(leaderboardRow));
}

function createLeaderboardDetailRow(leaderboardRow) {
  const tr = document.createElement("tr");
  tr.className = "leaderboard-detail-row";
  const td = document.createElement("td");
  td.colSpan = 8;

  const predictions = latestScoredPredictionsForAlias(leaderboardRow.model_alias);
  const cards = predictions.map((prediction) => {
    const result = predictionStore.results?.[String(prediction.match_id)];
    const score = prediction.score;
    const scorerHits = (score.goal_scorer_breakdown || [])
      .filter((scorer) => scorer.points)
      .map((scorer) => `${scorer.predicted} +${scorer.points}`)
      .join(" · ");
    return `
      <article class="leaderboard-match-card">
        <header>
          <span>Match ${chronologicalMatchNumber(prediction.match_id)}</span>
          <strong>${Number(score.total || 0)}/100</strong>
        </header>
        <h3>${escapeHtml(prediction.match)}</h3>
        <p class="card-result">${result ? `Final: ${escapeHtml(result.team1)} ${result.team1_score}-${result.team2_score} ${escapeHtml(result.team2)}` : "Final result unavailable"}</p>
        <dl>
          <dt>Prediction</dt>
          <dd>${escapeHtml(prediction.prediction)} · ${escapeHtml(prediction.scoreline)}</dd>
        </dl>
        <div class="card-score-grid">
          ${cardScorePart("Result", score.result, 50)}
          ${cardScorePart("Score", score.scoreline, 25)}
          ${cardScorePart("Difference", score.goal_difference, 10)}
          ${cardScorePart("Scorers", score.goal_scorers, 15)}
        </div>
        <p class="card-scorer-hits">${escapeHtml(scorerHits || "No predicted scorer hit")}</p>
      </article>
    `;
  }).join("");

  td.innerHTML = `
    <div class="leaderboard-carousel" aria-label="${escapeHtml(leaderboardRow.model_alias)} match score breakdown">
      ${cards || '<p class="empty-state">No scored matches yet.</p>'}
    </div>
  `;
  tr.append(td);
  return tr;
}

function latestScoredPredictionsForAlias(alias) {
  const byMatch = new Map();
  for (const prediction of allPredictions) {
    if (aliasForRow(prediction) === alias && prediction.score && prediction.match_id !== undefined) {
      byMatch.set(Number(prediction.match_id), prediction);
    }
  }
  return Array.from(byMatch.values()).sort(
    (a, b) => chronologicalMatchNumber(a.match_id) - chronologicalMatchNumber(b.match_id),
  );
}

function chronologicalMatchNumber(matchId) {
  const ordered = chronologicalMatches();
  return ordered.findIndex((match) => Number(match.match_id) === Number(matchId)) + 1;
}

function cardScorePart(label, points, maximum) {
  return `
    <div>
      <span>${escapeHtml(label)}</span>
      <strong>${Number(points || 0)}<small>/${maximum}</small></strong>
    </div>
  `;
}

function wireTabs() {
  const tabs = {
    predictionsTab: "predictionsView",
    leaderboardTab: "modelLeaderboardView",
    analysisTab: "analysisView",
    rulesTab: "rulesView",
  };
  const matchSummaryCard = document.getElementById("matchSummaryCard");
  let analysisDrawn = false;

  for (const [tabId, viewId] of Object.entries(tabs)) {
    document.getElementById(tabId).addEventListener("click", () => {
      for (const [otherTab, otherView] of Object.entries(tabs)) {
        const isActive = otherTab === tabId;
        document.getElementById(otherTab).classList.toggle("active", isActive);
        document.getElementById(otherView).hidden = !isActive;
      }
      matchSummaryCard.hidden = tabId !== "predictionsTab";
      if (tabId === "analysisTab" && !analysisDrawn) {
        renderAnalysis();
        analysisDrawn = true;
      }
    });
  }
}

function wireDownload() {
  const button = document.getElementById("downloadDataBtn");
  if (!button) return;
  button.addEventListener("click", async () => {
    const originalLabel = button.textContent;
    button.disabled = true;
    button.textContent = "Preparing…";
    try {
      const matchIds = [...new Set(allPredictions.map((p) => Number(p.match_id)))]
        .filter((id) => Number.isFinite(id))
        .sort((a, b) => a - b);

      const contextFiles = {};
      await Promise.all(
        matchIds.map(async (id) => {
          try {
            const response = await fetch(`/data/match_${id}.json`, { cache: "no-store" });
            if (response.ok) contextFiles[id] = await response.json();
          } catch {
            /* skip missing context files */
          }
        }),
      );

      const bundle = { ...predictionStore, context_files: contextFiles };
      const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "fifa_wc_2026_predictions_full.json";
      document.body.append(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } finally {
      button.disabled = false;
      button.textContent = originalLabel;
    }
  });
}

function matchIdFromHash() {
  const match = window.location.hash.match(/^#match-(\d+)$/);
  if (!match) return null;
  return Number(chronologicalMatches()[Number(match[1]) - 1]?.match_id || 0) || null;
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
  const colors = pickColors[value] || pickColors.Draw;
  span.className = `pick ${colors === pickColors.Draw ? "draw-pick" : "team-pick"}`;
  span.style.setProperty("--pick-bg", colors.bg);
  span.style.setProperty("--pick-fg", colors.fg);
  span.textContent = value ?? "";
  td.append(span);
  return td;
}

function cellWithScore(score) {
  const td = document.createElement("td");
  const strong = document.createElement("strong");
  strong.className = score ? "total-score" : "total-score pending";
  strong.textContent = score ? `${score.total}/100` : "Pending";
  td.append(strong);
  return td;
}

function scoreBreakdownHtml(score) {
  if (!score) {
    return `
      <span class="detail-label">Score breakdown</span>
      <div class="score-pending">
        <strong>Pending result</strong>
        <p>Points will be calculated after the free final-score feed marks the match complete.</p>
      </div>
    `;
  }

  const scorerRows = (score.goal_scorer_breakdown || []).map((scorer) => `
    <li>
      <span>
        <strong>${escapeHtml(scorer.predicted)}</strong>
        <small>${scorer.matched_scorer ? `Scored as ${escapeHtml(scorer.matched_scorer)}` : "Did not score"}</small>
      </span>
      <b>${Number(scorer.points || 0)}</b>
    </li>
  `).join("");

  return `
    <div class="score-heading">
      <span class="detail-label">Score breakdown</span>
      <strong>${Number(score.total || 0)}<small>/100</small></strong>
    </div>
    <div class="score-categories">
      ${scoreCategoryHtml("Match result", score.result, 50, score.result === 50 ? "Correct outcome" : "Incorrect outcome")}
      ${scoreCategoryHtml("Scoreline", score.scoreline, 25, score.scoreline === 25 ? "Exact score" : "Not exact")}
      ${scoreCategoryHtml("Goal difference", score.goal_difference, 10, score.goal_difference === 10 ? "Correct margin" : "Incorrect margin")}
      ${scoreCategoryHtml("Goal scorers", score.goal_scorers, 15, `${Number(score.goal_scorers || 0) / 5} of 3 correct`)}
    </div>
    <ul class="goal-scorer-score-list">${scorerRows}</ul>
  `;
}

function scoreCategoryHtml(label, points, maximum, explanation) {
  return `
    <div>
      <span>${escapeHtml(label)}</span>
      <strong>${Number(points || 0)}<small>/${maximum}</small></strong>
      <small>${escapeHtml(explanation)}</small>
    </div>
  `;
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

function formatGoalScorers(value) {
  if (Array.isArray(value)) return value.join(", ");
  return value || "-";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

/* ============================================================
   ANALYSIS TAB
   Dependency-free, interactive SVG visualizations built from
   the same predictions/results/leaderboard already in memory.
   ============================================================ */

const SVGNS = "http://www.w3.org/2000/svg";
const ANALYSIS_PALETTE = [
  "#116149", "#b7322c", "#254e7b", "#c58a1d", "#7d3c98",
  "#0f7b8a", "#a0521d", "#4a5d23", "#8a1c5a", "#2c6e49",
  "#c0392b", "#2874a6", "#af7ac5", "#616a6b", "#d35400",
];

let analysisState = null;

function analysisTooltip() {
  let tip = document.getElementById("analysisTooltip");
  if (!tip) {
    tip = document.createElement("div");
    tip.id = "analysisTooltip";
    tip.className = "chart-tooltip";
    tip.hidden = true;
    document.body.append(tip);
  }
  return tip;
}

function showTip(html, event) {
  const tip = analysisTooltip();
  tip.innerHTML = html;
  tip.hidden = false;
  const pad = 14;
  let x = event.clientX + pad;
  let y = event.clientY + pad;
  const rect = tip.getBoundingClientRect();
  if (x + rect.width > window.innerWidth) x = event.clientX - rect.width - pad;
  if (y + rect.height > window.innerHeight) y = event.clientY - rect.height - pad;
  tip.style.left = `${Math.max(6, x)}px`;
  tip.style.top = `${Math.max(6, y)}px`;
}

function hideTip() {
  const tip = document.getElementById("analysisTooltip");
  if (tip) tip.hidden = true;
}

function svgEl(name, attrs = {}) {
  const el = document.createElementNS(SVGNS, name);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  return el;
}

function parseScoreline(scoreline) {
  const nums = String(scoreline || "").match(/\d+/g);
  if (!nums || nums.length < 2) return null;
  const a = Number(nums[nums.length - 2]);
  const b = Number(nums[nums.length - 1]);
  return { a, b, total: a + b, draw: a === b };
}

// -- Aggregate everything once ------------------------------------------------
function buildAnalysisData() {
  if (analysisState) return analysisState;

  const leaderboardRows = predictionStore.leaderboard?.rows || [];
  const orderedMatches = chronologicalMatches();
  const matchNumber = new Map(orderedMatches.map((m, i) => [Number(m.match_id), i + 1]));

  const aliases = leaderboardRows.map((r) => r.model_alias);
  const colorFor = new Map(aliases.map((a, i) => [a, ANALYSIS_PALETTE[i % ANALYSIS_PALETTE.length]]));

  // latest scored prediction per (matchId, alias)
  const latest = new Map();
  for (const p of allPredictions) {
    if (!p.score) continue;
    const alias = aliasForRow(p);
    if (!colorFor.has(alias)) continue;
    latest.set(`${p.match_id}::${alias}`, p);
  }
  const scored = Array.from(latest.values());

  // Per-model aggregates
  const perModel = new Map();
  for (const alias of aliases) {
    perModel.set(alias, {
      alias,
      color: colorFor.get(alias),
      preds: [],
      draws: 0,
      goalsPredicted: 0,
      confidenceSum: 0,
      confidenceN: 0,
    });
  }
  // majority pick per match for contrarian metric
  const pickByMatch = new Map();
  for (const p of scored) {
    if (!pickByMatch.has(p.match_id)) pickByMatch.set(p.match_id, new Map());
    const m = pickByMatch.get(p.match_id);
    m.set(p.prediction, (m.get(p.prediction) || 0) + 1);
  }
  const majority = new Map();
  for (const [mid, counts] of pickByMatch) {
    majority.set(mid, [...counts.entries()].sort((a, b) => b[1] - a[1])[0][0]);
  }

  for (const p of scored) {
    const bucket = perModel.get(aliasForRow(p));
    bucket.preds.push(p);
    const sl = parseScoreline(p.scoreline);
    if (sl) { bucket.goalsPredicted += sl.total; if (sl.draw) bucket.draws += 1; }
    if (p.confidence != null) { bucket.confidenceSum += Number(p.confidence); bucket.confidenceN += 1; }
  }
  for (const bucket of perModel.values()) {
    const n = bucket.preds.length || 1;
    bucket.drawRate = bucket.draws / n;
    bucket.avgGoals = bucket.goalsPredicted / n;
    bucket.avgConfidence = bucket.confidenceN ? bucket.confidenceSum / bucket.confidenceN : 0;
    bucket.contrarian = bucket.preds.filter((p) => p.prediction !== majority.get(p.match_id)).length / n;
  }

  // Cumulative points race across chronological matches
  const completedMatchIds = orderedMatches
    .map((m) => Number(m.match_id))
    .filter((id) => predictionStore.results?.[String(id)]);
  const race = new Map();
  const perMatch = new Map();
  for (const alias of aliases) {
    let running = 0;
    const series = [];
    const pm = [];
    for (const id of completedMatchIds) {
      const p = latest.get(`${id}::${alias}`);
      const v = p ? Number(p.score.total || 0) : 0;
      pm.push({ v, has: !!p });
      running += v;
      series.push(running);
    }
    race.set(alias, series);
    perMatch.set(alias, pm);
  }

  // Margin vs field: cumulative points minus the per-match average model
  const n = completedMatchIds.length;
  const fieldAvg = [];
  for (let i = 0; i < n; i++) {
    fieldAvg.push(aliases.reduce((s, a) => s + race.get(a)[i], 0) / (aliases.length || 1));
  }
  const margin = new Map(aliases.map((a) => [a, race.get(a).map((v, i) => v - fieldAvg[i])]));

  // Rank at each match (1 = leader)
  const rankSeries = new Map(aliases.map((a) => [a, []]));
  for (let i = 0; i < n; i++) {
    const ordered = [...aliases].sort((a, b) => race.get(b)[i] - race.get(a)[i]);
    ordered.forEach((a, idx) => rankSeries.get(a).push(idx + 1));
  }

  // Head-to-head: fraction of shared matches where row out-scored col
  const h2h = new Map();
  for (const a of aliases) {
    h2h.set(a, new Map());
    for (const b of aliases) {
      if (a === b) { h2h.get(a).set(b, null); continue; }
      let wins = 0, comparable = 0;
      const pa = perMatch.get(a), pb = perMatch.get(b);
      for (let i = 0; i < n; i++) {
        if (!pa[i].has || !pb[i].has || pa[i].v === pb[i].v) continue;
        comparable += 1;
        if (pa[i].v > pb[i].v) wins += 1;
      }
      h2h.get(a).set(b, { wins, comparable, rate: comparable ? wins / comparable : 0 });
    }
  }

  // Confidence calibration (global + per model)
  const calibration = new Map();
  const bins = () => Array.from({ length: 11 }, () => ({ hit: 0, n: 0 }));
  const globalBins = bins();
  for (const alias of aliases) calibration.set(alias, bins());
  for (const p of scored) {
    if (p.confidence == null) continue;
    const idx = Math.round(Number(p.confidence) * 10);
    const hit = p.score.result === 50 ? 1 : 0;
    globalBins[idx].hit += hit; globalBins[idx].n += 1;
    const mb = calibration.get(aliasForRow(p))[idx];
    mb.hit += hit; mb.n += 1;
  }
  calibration.set("__all__", globalBins);

  // Goal scorer hype: predicted count + hit count from breakdown
  const scorerStats = new Map();
  for (const p of scored) {
    for (const gs of (p.score.goal_scorer_breakdown || [])) {
      const name = (gs.predicted || "").replace(/\s*\([^)]*\)\s*$/, "").trim();
      if (!name) continue;
      if (!scorerStats.has(name)) scorerStats.set(name, { name, predicted: 0, hits: 0 });
      const s = scorerStats.get(name);
      s.predicted += 1;
      if (Number(gs.points || 0) > 0) s.hits += 1;
    }
  }

  // Headline tournament stats
  const results = predictionStore.results || {};
  const resultList = Object.values(results);
  const actualAvgGoals = resultList.length
    ? resultList.reduce((s, r) => s + Number(r.team1_score || 0) + Number(r.team2_score || 0), 0) / resultList.length
    : 0;
  const predictedAvgGoals = scored.length
    ? scored.reduce((s, p) => s + (parseScoreline(p.scoreline)?.total || 0), 0) / scored.length
    : 0;
  const correctResults = scored.filter((p) => p.score.result === 50).length;
  const exactScores = scored.filter((p) => p.score.scoreline === 25).length;

  const best = [...leaderboardRows].sort((a, b) => b.average_points - a.average_points)[0];
  const value = [...leaderboardRows]
    .filter((r) => r.total_cost > 0)
    .sort((a, b) => (b.total_points / b.total_cost) - (a.total_points / a.total_cost))[0];

  analysisState = {
    aliases, colorFor, perModel, race, margin, rankSeries, h2h,
    completedMatchIds, matchNumber,
    calibration, scorerStats, leaderboardRows, orderedMatches, results,
    headline: {
      matches: completedMatchIds.length,
      predictions: scored.length,
      resultRate: scored.length ? correctResults / scored.length : 0,
      exactScores,
      actualAvgGoals, predictedAvgGoals,
      best, value,
    },
  };
  return analysisState;
}

// -- Top-level render ---------------------------------------------------------
function renderAnalysis() {
  const view = document.getElementById("analysisView");
  const data = buildAnalysisData();
  const h = data.headline;

  view.innerHTML = `
    <section class="panel analysis-intro">
      <p class="eyebrow">Deep dive</p>
      <h2>How the machines saw the World Cup</h2>
      <p>${formatInteger(h.predictions)} scored predictions from ${data.aliases.length} language models across ${h.matches} completed fixtures. Every chart below is live — hover, toggle and sort.</p>
    </section>

    <section class="metric-strip analysis-tiles" aria-label="Headline statistics">
      <div><span>Predictions scored</span><strong>${formatInteger(h.predictions)}</strong></div>
      <div><span>Correct results</span><strong>${Math.round(h.resultRate * 100)}%</strong></div>
      <div><span>Exact scorelines</span><strong>${formatInteger(h.exactScores)}</strong></div>
      <div><span>Goals · predicted vs real</span><strong>${h.predictedAvgGoals.toFixed(2)} <em>/ ${h.actualAvgGoals.toFixed(2)}</em></strong></div>
      <div><span>Most accurate</span><strong>${escapeHtml(h.best?.model_alias || "-")}</strong></div>
      <div><span>Best value / $</span><strong>${escapeHtml(h.value?.model_alias || "-")}</strong></div>
    </section>

    <section class="panel">
      <div class="panel-head chart-head">
        <div><p class="eyebrow">Do they know what they know?</p><h2>Confidence Calibration</h2></div>
        <p class="chart-note">A model is perfectly calibrated when its stated confidence equals its real win rate. Toggle any mix of models — the dashed diagonal is the ideal.</p>
      </div>
      <div id="calibLegend" class="chart-legend"></div>
      <div id="calibChart" class="chart-body"></div>
    </section>

    <section class="panel">
      <div class="panel-head chart-head">
        <div><p class="eyebrow">Momentum</p><h2>The Points Race</h2></div>
        <p class="chart-note">Cumulative points over completed matches. Click a model to isolate it.</p>
      </div>
      <div id="raceChart" class="chart-body"></div>
      <div id="raceLegend" class="chart-legend"></div>
    </section>

    <section class="panel">
      <div class="panel-head chart-head">
        <div><p class="eyebrow">Separation</p><h2>Margin vs. the Field</h2></div>
        <p class="chart-note">Cumulative points <em>above or below the average model</em>. Zero = dead average. This is the race with the tie removed. Click to isolate.</p>
      </div>
      <div id="marginChart" class="chart-body"></div>
      <div id="marginLegend" class="chart-legend"></div>
    </section>

    <section class="panel">
      <div class="panel-head chart-head">
        <div><p class="eyebrow">Volatility</p><h2>Rank Journey</h2></div>
        <p class="chart-note">Every model's leaderboard rank after each match. Top = 1st. Watch the lead changes. Click to isolate.</p>
      </div>
      <div id="bumpChart" class="chart-body"></div>
      <div id="bumpLegend" class="chart-legend"></div>
    </section>

    <section class="panel">
      <div class="panel-head chart-head">
        <div><p class="eyebrow">Who beats whom</p><h2>Head-to-Head Dominance</h2></div>
        <p class="chart-note">Each cell: how often the <b>row</b> model out-scored the <b>column</b> model on the same match. Greener = row wins more.</p>
      </div>
      <div id="h2hChart" class="chart-body"></div>
    </section>

    <section class="panel">
      <div class="panel-head chart-head">
        <div><p class="eyebrow">Efficiency frontier</p><h2>Accuracy vs. Cost</h2></div>
        <p class="chart-note">Up = more points. Left = cheaper. Bubble size = exact scorelines nailed.</p>
      </div>
      <div id="scatterChart" class="chart-body"></div>
    </section>

    <section class="panel">
      <div class="panel-head chart-head">
        <div><p class="eyebrow">Where points come from</p><h2>Score Anatomy</h2></div>
        <p class="chart-note">Every model's points split by category. Click a legend swatch to re-sort.</p>
      </div>
      <div id="anatomyLegend" class="chart-legend"></div>
      <div id="anatomyChart" class="chart-body"></div>
    </section>

    <section class="panel">
      <div class="panel-head chart-head">
        <div><p class="eyebrow">Player market</p><h2>Goal-Scorer Hype</h2></div>
        <p class="chart-note">Most-backed scorers. Filled = the pick actually scored at least once.</p>
      </div>
      <div id="scorerChart" class="chart-body"></div>
    </section>

    <section class="panel">
      <div class="panel-head chart-head">
        <div><p class="eyebrow">Personality</p><h2>Model Style DNA</h2></div>
        <p class="chart-note">Click a column header to sort. Bars are relative within each column.</p>
      </div>
      <div id="styleTable" class="style-table-wrap"></div>
    </section>
  `;

  drawRace(data);
  drawMarginRace(data);
  drawBumpChart(data);
  drawH2H(data);
  drawScatter(data);
  drawAnatomy(data);
  drawCalibration(data);
  drawScorerHype(data);
  drawStyleTable(data);
}

// -- 1. Points race -----------------------------------------------------------
function drawRace(data) {
  const host = document.getElementById("raceChart");
  const W = 900, H = 420, m = { t: 16, r: 16, b: 34, l: 46 };
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const n = data.completedMatchIds.length;
  const maxPts = Math.max(1, ...[...data.race.values()].map((s) => s[s.length - 1] || 0));
  const x = (i) => m.l + (n <= 1 ? 0 : (i / (n - 1)) * iw);
  const y = (v) => m.t + ih - (v / maxPts) * ih;

  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart-svg", preserveAspectRatio: "xMidYMid meet" });

  // gridlines + y labels
  const steps = 5;
  for (let s = 0; s <= steps; s++) {
    const v = (maxPts / steps) * s;
    const yy = y(v);
    svg.append(svgEl("line", { x1: m.l, y1: yy, x2: W - m.r, y2: yy, class: "grid-line" }));
    const t = svgEl("text", { x: m.l - 8, y: yy + 4, class: "axis-label", "text-anchor": "end" });
    t.textContent = Math.round(v);
    svg.append(t);
  }
  const xl = svgEl("text", { x: m.l, y: H - 8, class: "axis-label" });
  xl.textContent = "Match 1";
  svg.append(xl);
  const xr = svgEl("text", { x: W - m.r, y: H - 8, class: "axis-label", "text-anchor": "end" });
  xr.textContent = `Match ${n}`;
  svg.append(xr);

  const paths = new Map();
  for (const alias of data.aliases) {
    const series = data.race.get(alias);
    const d = series.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
    const path = svgEl("path", { d, fill: "none", stroke: data.colorFor.get(alias), "stroke-width": 2.4, class: "race-line", "stroke-linejoin": "round" });
    paths.set(alias, path);
    svg.append(path);
  }
  const focus = svgEl("circle", { r: 4.5, class: "race-focus", hidden: "" });
  svg.append(focus);
  host.replaceChildren(svg);

  // hover: find nearest match index, nearest line
  svg.addEventListener("mousemove", (e) => {
    const pt = svgPoint(svg, e);
    const i = Math.max(0, Math.min(n - 1, Math.round(((pt.x - m.l) / iw) * (n - 1))));
    let bestAlias = null, bestDy = Infinity;
    for (const alias of data.aliases) {
      if (host.dataset.isolate && host.dataset.isolate !== alias) continue;
      const dy = Math.abs(y(data.race.get(alias)[i]) - pt.y);
      if (dy < bestDy) { bestDy = dy; bestAlias = alias; }
    }
    if (!bestAlias) return;
    const val = data.race.get(bestAlias)[i];
    focus.setAttribute("cx", x(i)); focus.setAttribute("cy", y(val));
    focus.setAttribute("fill", data.colorFor.get(bestAlias)); focus.removeAttribute("hidden");
    showTip(`<strong style="color:${data.colorFor.get(bestAlias)}">${escapeHtml(bestAlias)}</strong><br>After match ${i + 1}: <b>${val}</b> pts`, e);
  });
  svg.addEventListener("mouseleave", () => { hideTip(); focus.setAttribute("hidden", ""); });

  // legend with isolate-on-click
  const legend = document.getElementById("raceLegend");
  legend.replaceChildren(...data.aliases.map((alias) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "legend-chip";
    chip.innerHTML = `<span class="legend-dot" style="background:${data.colorFor.get(alias)}"></span>${escapeHtml(alias)}`;
    chip.addEventListener("click", () => {
      const isolate = host.dataset.isolate === alias ? "" : alias;
      host.dataset.isolate = isolate;
      for (const [a, p] of paths) {
        const dim = isolate && isolate !== a;
        p.classList.toggle("dimmed", dim);
        p.setAttribute("stroke-width", isolate === a ? 3.6 : 2.4);
      }
      for (const c of legend.children) c.classList.toggle("legend-off", isolate && !c.contains(document.activeElement) && c !== chip);
      legend.querySelectorAll(".legend-chip").forEach((c) => c.classList.remove("legend-active"));
      if (isolate) chip.classList.add("legend-active");
      else for (const p of paths.values()) { p.classList.remove("dimmed"); p.setAttribute("stroke-width", 2.4); }
    });
    return chip;
  }));
}

// shared: legend chips that isolate one line among many
function isolateLegend(legendEl, aliases, colorFor, paths, host, baseWidth) {
  legendEl.replaceChildren(...aliases.map((alias) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "legend-chip";
    chip.innerHTML = `<span class="legend-dot" style="background:${colorFor(alias)}"></span>${escapeHtml(alias)}`;
    chip.addEventListener("click", () => {
      const isolate = host.dataset.isolate === alias ? "" : alias;
      host.dataset.isolate = isolate;
      for (const [a, p] of paths) {
        p.classList.toggle("dimmed", isolate && isolate !== a);
        p.setAttribute("stroke-width", isolate === a ? baseWidth + 1.4 : baseWidth);
      }
      legendEl.querySelectorAll(".legend-chip").forEach((c, i) =>
        c.classList.toggle("legend-active", isolate && aliases[i] === isolate));
    });
    return chip;
  }));
}

// -- 1b. Margin vs field ------------------------------------------------------
function drawMarginRace(data) {
  const host = document.getElementById("marginChart");
  const W = 900, H = 440, m = { t: 16, r: 96, b: 30, l: 46 };
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const n = data.completedMatchIds.length;
  const all = [...data.margin.values()].flat();
  const bound = Math.max(1, ...all.map((v) => Math.abs(v))) * 1.05;
  const x = (i) => m.l + (n <= 1 ? 0 : (i / (n - 1)) * iw);
  const y = (v) => m.t + ih / 2 - (v / bound) * (ih / 2);
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart-svg", preserveAspectRatio: "xMidYMid meet" });

  for (const g of [-1, -0.5, 0, 0.5, 1]) {
    const yy = y(g * bound);
    svg.append(svgEl("line", { x1: m.l, y1: yy, x2: W - m.r, y2: yy, class: g === 0 ? "zero-line" : "grid-line" }));
    const t = svgEl("text", { x: m.l - 8, y: yy + 4, class: "axis-label", "text-anchor": "end" });
    t.textContent = `${g > 0 ? "+" : ""}${Math.round(g * bound)}`;
    svg.append(t);
  }

  const finals = [];
  const paths = new Map();
  for (const alias of data.aliases) {
    const s = data.margin.get(alias);
    const d = s.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
    const path = svgEl("path", { d, fill: "none", stroke: data.colorFor.get(alias), "stroke-width": 2.4, class: "race-line", "stroke-linejoin": "round" });
    paths.set(alias, path);
    svg.append(path);
    finals.push({ alias, v: s[s.length - 1] });
  }
  // end labels, de-collided
  finals.sort((a, b) => b.v - a.v);
  let lastY = -Infinity;
  for (const f of finals) {
    let ly = y(f.v);
    if (ly - lastY < 13) ly = lastY + 13;
    lastY = ly;
    const t = svgEl("text", { x: W - m.r + 6, y: ly + 3, class: "end-label", fill: data.colorFor.get(f.alias) });
    t.textContent = f.alias;
    svg.append(t);
  }
  const focus = svgEl("circle", { r: 4.5, class: "race-focus", hidden: "" });
  svg.append(focus);
  host.replaceChildren(svg);

  svg.addEventListener("mousemove", (e) => {
    const pt = svgPoint(svg, e);
    const i = Math.max(0, Math.min(n - 1, Math.round(((pt.x - m.l) / iw) * (n - 1))));
    let best = null, bestDy = Infinity;
    for (const alias of data.aliases) {
      if (host.dataset.isolate && host.dataset.isolate !== alias) continue;
      const dy = Math.abs(y(data.margin.get(alias)[i]) - pt.y);
      if (dy < bestDy) { bestDy = dy; best = alias; }
    }
    if (!best) return;
    const v = data.margin.get(best)[i];
    focus.setAttribute("cx", x(i)); focus.setAttribute("cy", y(v));
    focus.setAttribute("fill", data.colorFor.get(best)); focus.removeAttribute("hidden");
    showTip(`<strong style="color:${data.colorFor.get(best)}">${escapeHtml(best)}</strong><br>After match ${i + 1}: <b>${v >= 0 ? "+" : ""}${v.toFixed(1)}</b> vs field`, e);
  });
  svg.addEventListener("mouseleave", () => { hideTip(); focus.setAttribute("hidden", ""); });
  isolateLegend(document.getElementById("marginLegend"), data.aliases, (a) => data.colorFor.get(a), paths, host, 2.4);
}

// -- 1c. Rank journey bump chart ---------------------------------------------
function drawBumpChart(data) {
  const host = document.getElementById("bumpChart");
  const N = data.aliases.length;
  const W = 900, rowGap = 30, m = { t: 16, r: 150, b: 30, l: 24 };
  const ih = (N - 1) * rowGap;
  const H = m.t + m.b + ih;
  const iw = W - m.l - m.r;
  const n = data.completedMatchIds.length;
  const x = (i) => m.l + (n <= 1 ? 0 : (i / (n - 1)) * iw);
  const y = (rank) => m.t + (rank - 1) * rowGap;
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart-svg", preserveAspectRatio: "xMidYMid meet" });

  for (let r = 1; r <= N; r++) {
    svg.append(svgEl("line", { x1: m.l, y1: y(r), x2: W - m.r, y2: y(r), class: "grid-line" }));
    const t = svgEl("text", { x: m.l - 8, y: y(r) + 4, class: "axis-label", "text-anchor": "end" });
    t.textContent = r;
    svg.append(t);
  }

  const paths = new Map();
  for (const alias of data.aliases) {
    const s = data.rankSeries.get(alias);
    const d = s.map((r, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(r).toFixed(1)}`).join(" ");
    const path = svgEl("path", { d, fill: "none", stroke: data.colorFor.get(alias), "stroke-width": 2.6, class: "race-line", "stroke-linejoin": "round", "stroke-linecap": "round" });
    paths.set(alias, path);
    svg.append(path);
    const finalRank = s[s.length - 1];
    const t = svgEl("text", { x: W - m.r + 8, y: y(finalRank) + 3, class: "end-label", fill: data.colorFor.get(alias) });
    t.textContent = `${finalRank}. ${alias}`;
    svg.append(t);
  }
  const focus = svgEl("circle", { r: 5, class: "race-focus", hidden: "" });
  svg.append(focus);
  host.replaceChildren(svg);

  svg.addEventListener("mousemove", (e) => {
    const pt = svgPoint(svg, e);
    const i = Math.max(0, Math.min(n - 1, Math.round(((pt.x - m.l) / iw) * (n - 1))));
    let best = null, bestDy = Infinity;
    for (const alias of data.aliases) {
      if (host.dataset.isolate && host.dataset.isolate !== alias) continue;
      const dy = Math.abs(y(data.rankSeries.get(alias)[i]) - pt.y);
      if (dy < bestDy) { bestDy = dy; best = alias; }
    }
    if (!best) return;
    const r = data.rankSeries.get(best)[i];
    focus.setAttribute("cx", x(i)); focus.setAttribute("cy", y(r));
    focus.setAttribute("fill", data.colorFor.get(best)); focus.removeAttribute("hidden");
    showTip(`<strong style="color:${data.colorFor.get(best)}">${escapeHtml(best)}</strong><br>After match ${i + 1}: rank <b>#${r}</b> of ${N}`, e);
  });
  svg.addEventListener("mouseleave", () => { hideTip(); focus.setAttribute("hidden", ""); });
  isolateLegend(document.getElementById("bumpLegend"), data.aliases, (a) => data.colorFor.get(a), paths, host, 2.6);
}

// -- 1d. Head-to-head dominance matrix ---------------------------------------
function drawH2H(data) {
  const host = document.getElementById("h2hChart");
  const aliases = data.aliases;
  const N = aliases.length;
  const cell = 34, labelL = 140, labelT = 130, pad = 6;
  const W = labelL + N * cell + pad;
  const H = labelT + N * cell + pad;
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart-svg h2h-svg", preserveAspectRatio: "xMidYMid meet" });

  aliases.forEach((a, r) => {
    const ty = svgEl("text", { x: labelL - 8, y: labelT + r * cell + cell / 2 + 4, class: "bar-name", "text-anchor": "end" });
    ty.textContent = a;
    svg.append(ty);
    const cx = labelL + r * cell + cell / 2;
    const tx = svgEl("text", { x: cx, y: labelT - 8, class: "bar-name h2h-coltext", "text-anchor": "start", transform: `rotate(-45 ${cx} ${labelT - 8})` });
    tx.textContent = a;
    svg.append(tx);
  });

  aliases.forEach((rowA, r) => {
    aliases.forEach((colB, c) => {
      const gx = labelL + c * cell, gy = labelT + r * cell;
      const info = data.h2h.get(rowA).get(colB);
      if (info === null) {
        svg.append(svgEl("rect", { x: gx + 1, y: gy + 1, width: cell - 2, height: cell - 2, fill: "#2f2a24", "fill-opacity": 0.14 }));
        return;
      }
      const rate = info.rate;
      // diverging: red (loses) -> pale -> green (wins) around 0.5
      const t = (rate - 0.5) * 2; // -1..1
      const col = t >= 0
        ? mix([231, 221, 178], [17, 97, 73], t)
        : mix([231, 221, 178], [183, 50, 44], -t);
      const rect = svgEl("rect", { x: gx + 1, y: gy + 1, width: cell - 2, height: cell - 2, fill: `rgb(${col.join(",")})`, class: "h2h-cell" });
      rect.addEventListener("mousemove", (e) => showTip(
        `<strong>${escapeHtml(rowA)}</strong> vs <strong>${escapeHtml(colB)}</strong><br>`
        + `Out-scored it in <b>${info.wins}</b> of ${info.comparable} decisive matches<br>`
        + `<b>${Math.round(rate * 100)}%</b> win rate`, e));
      rect.addEventListener("mouseleave", hideTip);
      svg.append(rect);
      const label = svgEl("text", { x: gx + cell / 2, y: gy + cell / 2 + 4, class: "h2h-val", "text-anchor": "middle", fill: Math.abs(t) > 0.55 ? "#fff" : "#14110f" });
      label.textContent = Math.round(rate * 100);
      svg.append(label);
    });
  });
  host.replaceChildren(svg);
}

function mix(a, b, t) {
  return a.map((v, i) => Math.round(v + (b[i] - v) * t));
}

// -- 2. Accuracy vs cost scatter ---------------------------------------------
function drawScatter(data) {
  const host = document.getElementById("scatterChart");
  const rows = data.leaderboardRows;
  const W = 900, H = 440, m = { t: 20, r: 24, b: 46, l: 54 };
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const costs = rows.map((r) => r.total_cost || 0);
  const pts = rows.map((r) => r.total_points || 0);
  const maxCost = Math.max(...costs) * 1.08 || 1;
  const minPts = Math.min(...pts) * 0.96, maxPts = Math.max(...pts) * 1.02;
  const maxExact = Math.max(1, ...rows.map((r) => r.exact_scores || 0));
  const x = (v) => m.l + (v / maxCost) * iw;
  const y = (v) => m.t + ih - ((v - minPts) / (maxPts - minPts || 1)) * ih;

  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart-svg", preserveAspectRatio: "xMidYMid meet" });
  for (let s = 0; s <= 4; s++) {
    const yy = m.t + (ih / 4) * s;
    svg.append(svgEl("line", { x1: m.l, y1: yy, x2: W - m.r, y2: yy, class: "grid-line" }));
    const v = maxPts - ((maxPts - minPts) / 4) * s;
    const t = svgEl("text", { x: m.l - 8, y: yy + 4, class: "axis-label", "text-anchor": "end" });
    t.textContent = Math.round(v);
    svg.append(t);
  }
  const ax = svgEl("text", { x: m.l + iw / 2, y: H - 10, class: "axis-title", "text-anchor": "middle" });
  ax.textContent = "Total cost to run (USD) →";
  svg.append(ax);
  const ay = svgEl("text", { x: 16, y: m.t + ih / 2, class: "axis-title", "text-anchor": "middle", transform: `rotate(-90 16 ${m.t + ih / 2})` });
  ay.textContent = "Total points →";
  svg.append(ay);

  rows.forEach((r) => {
    const cx = x(r.total_cost || 0), cy = y(r.total_points || 0);
    const rad = 6 + (r.exact_scores / maxExact) * 16;
    const g = svgEl("g", { class: "scatter-node" });
    const c = svgEl("circle", { cx, cy, r: rad, fill: data.colorFor.get(r.model_alias), "fill-opacity": 0.72, stroke: "#14110f", "stroke-width": 1.2 });
    g.append(c);
    const label = svgEl("text", { x: cx, y: cy - rad - 5, class: "scatter-label", "text-anchor": "middle" });
    label.textContent = r.model_alias;
    g.append(label);
    g.addEventListener("mousemove", (e) => showTip(
      `<strong style="color:${data.colorFor.get(r.model_alias)}">${escapeHtml(r.model_alias)}</strong><br>`
      + `${r.total_points} pts · ${formatCurrency(r.total_cost || 0)}<br>`
      + `${r.correct_results} correct · ${r.exact_scores} exact scores<br>`
      + `<b>${(r.total_points / (r.total_cost || 1e-9)).toFixed(0)}</b> pts per $`, e));
    g.addEventListener("mouseleave", hideTip);
    svg.append(g);
  });
  host.replaceChildren(svg);
}

// -- 3. Score anatomy stacked bars -------------------------------------------
function drawAnatomy(data) {
  const cats = [
    { key: "result_points", label: "Result", color: "#116149" },
    { key: "scoreline_points", label: "Scoreline", color: "#c58a1d" },
    { key: "goal_difference_points", label: "Goal diff", color: "#254e7b" },
    { key: "goal_scorer_points", label: "Scorers", color: "#b7322c" },
  ];
  const state = { sortKey: "total_points" };
  const legend = document.getElementById("anatomyLegend");
  legend.replaceChildren(...cats.map((c) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "legend-chip";
    chip.innerHTML = `<span class="legend-dot" style="background:${c.color}"></span>${c.label}`;
    chip.addEventListener("click", () => { state.sortKey = c.key; render(); });
    return chip;
  }));

  function render() {
    const host = document.getElementById("anatomyChart");
    const rows = [...data.leaderboardRows].sort((a, b) => (b[state.sortKey] || 0) - (a[state.sortKey] || 0));
    const W = 900, rowH = 34, m = { t: 8, r: 20, b: 28, l: 154 };
    const H = m.t + m.b + rows.length * rowH;
    const iw = W - m.l - m.r;
    const maxTotal = Math.max(...rows.map((r) => r.total_points || 0)) || 1;
    const x = (v) => (v / maxTotal) * iw;
    const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart-svg", preserveAspectRatio: "xMidYMid meet" });

    rows.forEach((r, i) => {
      const yy = m.t + i * rowH + 4;
      const bh = rowH - 12;
      const name = svgEl("text", { x: m.l - 10, y: yy + bh / 2 + 4, class: "bar-name", "text-anchor": "end" });
      name.textContent = r.model_alias;
      svg.append(name);
      let acc = 0;
      for (const c of cats) {
        const val = r[c.key] || 0;
        const seg = svgEl("rect", { x: m.l + x(acc), y: yy, width: Math.max(0, x(val)), height: bh, fill: c.color, class: "anatomy-seg" });
        seg.addEventListener("mousemove", (e) => showTip(`<strong>${escapeHtml(r.model_alias)}</strong><br>${c.label}: <b>${val}</b> pts`, e));
        seg.addEventListener("mouseleave", hideTip);
        svg.append(seg);
        acc += val;
      }
      const tot = svgEl("text", { x: m.l + x(acc) + 6, y: yy + bh / 2 + 4, class: "bar-total" });
      tot.textContent = r.total_points;
      svg.append(tot);
    });
    host.replaceChildren(svg);
    legend.querySelectorAll(".legend-chip").forEach((c, i) => c.classList.toggle("legend-active", cats[i].key === state.sortKey));
  }
  render();
}

// -- 4. Confidence calibration (multi-select) --------------------------------
function drawCalibration(data) {
  const seriesKeys = ["__all__", ...data.aliases];
  const labelFor = (key) => (key === "__all__" ? "All models (aggregate)" : key);
  const colorFor = (key) => (key === "__all__" ? "#14110f" : data.colorFor.get(key));
  const selected = new Set(["__all__"]);

  const legend = document.getElementById("calibLegend");
  legend.replaceChildren(...seriesKeys.map((key) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "legend-chip";
    chip.innerHTML = `<span class="legend-dot" style="background:${colorFor(key)}"></span>${escapeHtml(labelFor(key))}`;
    chip.addEventListener("click", () => {
      if (selected.has(key)) {
        if (selected.size > 1) selected.delete(key);
      } else {
        selected.add(key);
      }
      updateChips();
      render();
    });
    return chip;
  }));

  function updateChips() {
    legend.querySelectorAll(".legend-chip").forEach((chip, i) => {
      chip.classList.toggle("legend-active", selected.has(seriesKeys[i]));
    });
  }

  function seriesPoints(key) {
    const bins = data.calibration.get(key) || [];
    const points = [];
    bins.forEach((b, idx) => { if (b.n >= 3) points.push({ conf: idx / 10, acc: b.hit / b.n, n: b.n }); });
    return points;
  }

  function render() {
    const host = document.getElementById("calibChart");
    const W = 900, H = 460, m = { t: 20, r: 24, b: 48, l: 52 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const x = (v) => m.l + v * iw;
    const y = (v) => m.t + ih - v * ih;
    const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart-svg", preserveAspectRatio: "xMidYMid meet" });

    for (let s = 0; s <= 5; s++) {
      const g = s / 5;
      svg.append(svgEl("line", { x1: m.l, y1: y(g), x2: W - m.r, y2: y(g), class: "grid-line" }));
      const ty = svgEl("text", { x: m.l - 8, y: y(g) + 4, class: "axis-label", "text-anchor": "end" });
      ty.textContent = `${g * 100}%`; svg.append(ty);
      const tx = svgEl("text", { x: x(g), y: H - 20, class: "axis-label", "text-anchor": "middle" });
      tx.textContent = `${g * 100}%`; svg.append(tx);
    }
    // perfect-calibration diagonal
    svg.append(svgEl("line", { x1: x(0), y1: y(0), x2: x(1), y2: y(1), class: "calib-ideal" }));
    const idealLabel = svgEl("text", { x: x(0.82), y: y(0.82) - 8, class: "axis-label", "text-anchor": "middle" });
    idealLabel.textContent = "perfect"; svg.append(idealLabel);
    svg.append(Object.assign(svgEl("text", { x: m.l + iw / 2, y: H - 4, class: "axis-title", "text-anchor": "middle" }), { textContent: "Stated confidence" }));
    svg.append(Object.assign(svgEl("text", { x: 15, y: m.t + ih / 2, class: "axis-title", "text-anchor": "middle", transform: `rotate(-90 15 ${m.t + ih / 2})` }), { textContent: "Actual win rate" }));

    // draw one line + dots per selected series
    for (const key of seriesKeys) {
      if (!selected.has(key)) continue;
      const color = colorFor(key);
      const points = seriesPoints(key);
      if (points.length > 1) {
        const d = points.map((p, i) => `${i ? "L" : "M"}${x(p.conf).toFixed(1)},${y(p.acc).toFixed(1)}`).join(" ");
        svg.append(svgEl("path", { d, fill: "none", stroke: color, "stroke-width": key === "__all__" ? 3.2 : 2.2, "stroke-linejoin": "round", "stroke-opacity": key === "__all__" ? 1 : 0.85 }));
      }
      for (const p of points) {
        const dot = svgEl("circle", { cx: x(p.conf), cy: y(p.acc), r: 4 + Math.min(8, p.n / 14), fill: color, stroke: "#fff", "stroke-width": 1.2 });
        dot.addEventListener("mousemove", (e) => showTip(
          `<strong style="color:${color === "#14110f" ? "#fff" : color}">${escapeHtml(labelFor(key))}</strong><br>`
          + `Said <b>${Math.round(p.conf * 100)}%</b> confident<br>Won <b>${Math.round(p.acc * 100)}%</b> of the time<br><small>${p.n} predictions</small>`, e));
        dot.addEventListener("mouseleave", hideTip);
        svg.append(dot);
      }
    }
    host.replaceChildren(svg);
  }

  updateChips();
  render();
}

// -- 5. Goal scorer hype ------------------------------------------------------
function drawScorerHype(data) {
  const host = document.getElementById("scorerChart");
  const top = [...data.scorerStats.values()].sort((a, b) => b.predicted - a.predicted).slice(0, 16);
  const W = 900, rowH = 30, m = { t: 8, r: 60, b: 28, l: 150 };
  const H = m.t + m.b + top.length * rowH;
  const iw = W - m.l - m.r;
  const maxP = Math.max(...top.map((s) => s.predicted)) || 1;
  const x = (v) => (v / maxP) * iw;
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart-svg", preserveAspectRatio: "xMidYMid meet" });

  top.forEach((s, i) => {
    const yy = m.t + i * rowH + 4;
    const bh = rowH - 10;
    const name = svgEl("text", { x: m.l - 10, y: yy + bh / 2 + 4, class: "bar-name", "text-anchor": "end" });
    name.textContent = s.name;
    svg.append(name);
    // total picks (light) + hit portion (filled green)
    svg.append(svgEl("rect", { x: m.l, y: yy, width: x(s.predicted), height: bh, fill: "#d8cbb2", class: "scorer-bg" }));
    const scored = s.hits > 0;
    const bar = svgEl("rect", { x: m.l, y: yy, width: x(s.predicted), height: bh, fill: scored ? "#116149" : "#b7322c", "fill-opacity": scored ? 0.9 : 0.5, class: "scorer-bar" });
    bar.addEventListener("mousemove", (e) => showTip(
      `<strong>${escapeHtml(s.name)}</strong><br>Backed <b>${s.predicted}</b> times<br>${scored ? `Actually scored — <b>${s.hits}</b> correct picks` : "Never scored in the data"}`, e));
    bar.addEventListener("mouseleave", hideTip);
    svg.append(bar);
    const val = svgEl("text", { x: m.l + x(s.predicted) + 6, y: yy + bh / 2 + 4, class: "bar-total" });
    val.textContent = `${s.predicted}${scored ? " ✓" : ""}`;
    svg.append(val);
  });
  host.replaceChildren(svg);
}

// -- 6. Style DNA sortable table ---------------------------------------------
function drawStyleTable(data) {
  const cols = [
    { key: "avgPoints", label: "Avg pts", fmt: (v) => v.toFixed(1), get: (m, r) => r.average_points },
    { key: "drawRate", label: "Draw %", fmt: (v) => `${Math.round(v * 100)}%`, get: (m) => m.drawRate },
    { key: "avgGoals", label: "Avg goals", fmt: (v) => v.toFixed(2), get: (m) => m.avgGoals },
    { key: "avgConfidence", label: "Boldness", fmt: (v) => `${Math.round(v * 100)}%`, get: (m) => m.avgConfidence },
    { key: "contrarian", label: "Contrarian", fmt: (v) => `${Math.round(v * 100)}%`, get: (m) => m.contrarian },
  ];
  const rowData = data.aliases.map((alias) => {
    const pm = data.perModel.get(alias);
    const lb = data.leaderboardRows.find((r) => r.model_alias === alias) || {};
    const values = {};
    for (const c of cols) values[c.key] = c.get(pm, lb) || 0;
    return { alias, color: pm.color, values };
  });
  const maxes = {};
  for (const c of cols) maxes[c.key] = Math.max(...rowData.map((r) => r.values[c.key])) || 1;
  const state = { key: "avgPoints", dir: -1 };

  function render() {
    const host = document.getElementById("styleTable");
    const sorted = [...rowData].sort((a, b) => (a.values[state.key] - b.values[state.key]) * state.dir);
    const table = document.createElement("table");
    table.className = "style-table";
    const thead = document.createElement("thead");
    const htr = document.createElement("tr");
    htr.append(Object.assign(document.createElement("th"), { textContent: "Model" }));
    for (const c of cols) {
      const th = document.createElement("th");
      const btn = document.createElement("button");
      btn.type = "button"; btn.className = "sort-button" + (state.key === c.key ? " active" : "");
      btn.innerHTML = `<span>${c.label}</span><b>${state.key === c.key ? (state.dir < 0 ? "↓" : "↑") : ""}</b>`;
      btn.onclick = () => {
        if (state.key === c.key) state.dir *= -1;
        else { state.key = c.key; state.dir = -1; }
        render();
      };
      th.append(btn); htr.append(th);
    }
    thead.append(htr); table.append(thead);
    const tbody = document.createElement("tbody");
    for (const r of sorted) {
      const tr = document.createElement("tr");
      const nameTd = document.createElement("td");
      nameTd.innerHTML = `<span class="style-name"><span class="legend-dot" style="background:${r.color}"></span>${escapeHtml(r.alias)}</span>`;
      tr.append(nameTd);
      for (const c of cols) {
        const td = document.createElement("td");
        const pct = Math.max(4, (r.values[c.key] / maxes[c.key]) * 100);
        td.innerHTML = `<span class="cell-bar" style="--w:${pct}%;--c:${r.color}"></span><span class="cell-val">${c.fmt(r.values[c.key])}</span>`;
        tr.append(td);
      }
      tbody.append(tr);
    }
    table.append(tbody);
    host.replaceChildren(table);
  }
  render();
}

function svgPoint(svg, event) {
  const rect = svg.getBoundingClientRect();
  const vb = svg.viewBox.baseVal;
  return {
    x: ((event.clientX - rect.left) / rect.width) * vb.width,
    y: ((event.clientY - rect.top) / rect.height) * vb.height,
  };
}
