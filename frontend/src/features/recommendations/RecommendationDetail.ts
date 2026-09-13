import type { components } from "../../api/generated";
import { escapeHtml } from "../proftest/rendering";

type Reason = components["schemas"]["ReasonResponse"];
type Recommendation = components["schemas"]["RecommendationResponse"];

export function renderRecommendationDetail(recommendation: Recommendation): string {
  const fitReasons = recommendation.reasons.map((reason) => reasonLine(reason, "+", "fit")).join("");
  const antiReasons = recommendation.antiFitReasons.map((reason) => reasonLine(reason, "−", "anti-fit")).join("");
  const areas = Object.entries(recommendation.areaShare).sort(([, left], [, right]) => Number(right) - Number(left)).slice(0, 5).map(([area, share]) => `<li><span>${escapeHtml(areaLabel(area))}</span><strong>${Math.round(Number(share) * 100)}%</strong><i><b style="width:${Math.round(Number(share) * 100)}%"></b></i></li>`).join("");
  const groups = Object.entries(recommendation.subjectGroupShare).sort(([, left], [, right]) => Number(right) - Number(left)).slice(0, 5).map(([group, share]) => `<li><span>${escapeHtml(group)}</span><strong>${Math.round(Number(share) * 100)}%</strong></li>`).join("");
  const semesters = Object.entries(recommendation.semesterDistribution).sort(([left], [right]) => Number(left) - Number(right)).map(([semester, share]) => `<li><span>${escapeHtml(semester)} семестр</span><strong>${Math.round(Number(share) * 100)}%</strong></li>`).join("");
  const distinctive = recommendation.distinctiveSubjects.map((subject) => `<span class="subject-pill">${escapeHtml(subject)}</span>`).join("");
  return `<article class="detail-card" data-testid="proftest-detail-card"><div class="detail-heading"><div><p class="eyebrow">${escapeHtml(recommendation.programCode)}</p><h2>${escapeHtml(recommendation.programName)}</h2></div><strong class="fit-score">${recommendation.contentFit}<small>/100</small></strong></div><div class="reason-columns"><section><h3>Почему подходит</h3>${fitReasons || "<p class='muted'>Явных положительных сигналов пока нет.</p>"}</section><section><h3>Что может не понравиться</h3>${antiReasons || "<p class='muted'>Сильных anti-interest конфликтов не найдено.</p>"}</section></div><section><h3>Области учебного плана</h3><ul class="area-list">${areas || "<li>Нет детализации</li>"}</ul></section><div class="detail-grids"><section><h3>Блоки дисциплин</h3><ul class="compact-list">${groups || "<li>Нет детализации</li>"}</ul></section><section><h3>Семестры</h3><ul class="compact-list">${semesters || "<li>Нет детализации</li>"}</ul></section></div><section><h3>Отличительные дисциплины</h3><div class="subject-pills">${distinctive || "<span class='muted'>Каталог пока не выделил отличительные дисциплины.</span>"}</div></section><p class="muted">Workload readiness, Career Fit и Admission Fit: пока недоступны — они не влияют на Content Fit.</p></article>`;
}

function reasonLine(reason: Reason, marker: string, kind: string): string {
  return `<p class="reason-line ${kind}"><b>${marker}</b><span>${escapeHtml(reason.text)}${Number(reason.workload) > 0 ? ` <small>${escapeHtml(String(reason.workload))} workload</small>` : ""}${reason.sourceNames.length > 0 ? ` <small>${escapeHtml(reason.sourceNames.join(", "))}</small>` : ""}</span></p>`;
}

function areaLabel(area: string): string {
  const labels: Record<string, string> = {
    mathematics_statistics: "Математика и статистика",
    computer_science_data: "Компьютерные науки и данные",
    physics_astronomy: "Физика и астрономия",
    chemistry_materials: "Химия и материалы",
    engineering_technology: "Инженерия и технологии",
    universal_interdisciplinary: "Универсальные дисциплины",
  };
  return labels[area] ?? area.replaceAll("_", " ");
}
