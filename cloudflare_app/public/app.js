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
  const predictionsTab = document.getElementById("predictionsTab");
  const leaderboardTab = document.getElementById("leaderboardTab");
  const rulesTab = document.getElementById("rulesTab");
  const predictionsView = document.getElementById("predictionsView");
  const modelLeaderboardView = document.getElementById("modelLeaderboardView");
  const rulesView = document.getElementById("rulesView");
  const matchSummaryCard = document.getElementById("matchSummaryCard");

  predictionsTab.addEventListener("click", () => {
    predictionsTab.classList.add("active");
    leaderboardTab.classList.remove("active");
    rulesTab.classList.remove("active");
    predictionsView.hidden = false;
    modelLeaderboardView.hidden = true;
    rulesView.hidden = true;
    matchSummaryCard.hidden = false;
  });

  leaderboardTab.addEventListener("click", () => {
    leaderboardTab.classList.add("active");
    predictionsTab.classList.remove("active");
    rulesTab.classList.remove("active");
    predictionsView.hidden = true;
    modelLeaderboardView.hidden = false;
    rulesView.hidden = true;
    matchSummaryCard.hidden = true;
  });

  rulesTab.addEventListener("click", () => {
    rulesTab.classList.add("active");
    predictionsTab.classList.remove("active");
    leaderboardTab.classList.remove("active");
    predictionsView.hidden = true;
    modelLeaderboardView.hidden = true;
    rulesView.hidden = false;
    matchSummaryCard.hidden = true;
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
