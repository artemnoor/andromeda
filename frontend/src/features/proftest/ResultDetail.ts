import type { components } from "../../api/generated";
import { areaLabel } from "./taxonomyLabels";
import { escapeHtml } from "./rendering";

type Reason = components["schemas"]["ReasonResponse"];
type Recommendation = components["schemas"]["RecommendationResponse"];

export function renderDetailMarkup(recommendation: Recommendation): string {
  const fitReasons = recommendation.reasons.map((reason) => reasonLine(reason, "+")).join("");
  const antiReasons = recommendation.antiFitReasons.map((reason) => reasonLine(reason, "−")).join("");
  const areas = Object.entries(recommendation.areaShare).sort(([, left], [, right]) => Number(right) - Number(left)).slice(0, 5).map(([area, share]) => `<li><span>${escapeHtml(areaLabel(area))}</span><strong>${Math.round(Number(share) * 100)}%</strong><i><b style="width:${Math.round(Number(share) * 100)}%"></b></i></li>`).join("");
  return `<article class="detail-card" data-testid="proftest-detail-card"><div class="detail-heading"><div><p class="eyebrow">${escapeHtml(recommendation.programCode)}</p><h2>${escapeHtml(recommendation.programName)}</h2></div><strong class="fit-score">${recommendation.contentFit}<small>/100</small></strong></div><div class="reason-columns"><section><h3>Почему подходит</h3>${fitReasons || "<p class='muted'>Явных положительных сигналов пока нет.</p>"}</section><section><h3>Что может не понравиться</h3>${antiReasons || "<p class='muted'>Сильных anti-interest конфликтов не найдено.</p>"}</section></div><section><h3>Структура учебного плана</h3><ul class="area-list">${areas || "<li>Нет детализации</li>"}</ul></section><p class="muted">Workload readiness, Career Fit и Admission Fit: пока недоступны — они не влияют на Content Fit.</p></article>`;
}

function reasonLine(reason: Reason, marker: string): string {
  return `<p class="reason-line"><b>${marker}</b><span>${escapeHtml(reason.text)}${Number(reason.workload) > 0 ? ` <small>${escapeHtml(String(reason.workload))} workload</small>` : ""}</span></p>`;
}
