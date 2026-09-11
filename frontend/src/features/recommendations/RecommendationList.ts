import type { components } from "../../api/generated";
import { escapeHtml } from "../proftest/rendering";

type Recommendation = components["schemas"]["RecommendationResponse"];
type Results = components["schemas"]["ProftestResultsResponse"];

export function renderRecommendationList(results: Results): string {
  return `<section class="results-head"><p class="eyebrow">Твой профиль содержания</p><h1>Программы, с которых стоит начать</h1><p class="lead">Это не ярлык и не обещание профессии. Ниже — сопоставление твоих ответов с тем, что реально изучают на программах.</p><div class="profile-pills">${results.profile.interests.slice(0, 4).map((interest) => `<span>${escapeHtml(areaLabel(interest))}</span>`).join("")}</div></section><section class="results-list" data-testid="proftest-results"><div class="section-heading"><div><p class="eyebrow">Content Fit</p><h2>TOP программ</h2></div><span class="count">${results.recommendations.length} результатов</span></div>${results.recommendations.map((recommendation, index) => recommendationCard(recommendation, index)).join("")}</section><div id="proftest-detail"></div><div class="test-actions results-actions"><button class="secondary-button" data-testid="proftest-restart" type="button">Пройти заново</button></div>`;
}

function recommendationCard(recommendation: Recommendation, index: number): string {
  const topReason = recommendation.reasons[0]?.text ?? recommendation.antiFitReasons[0]?.text ?? "Сопоставление построено по структуре учебного плана.";
  return `<article class="result-card" data-testid="result-card"><div><p class="eyebrow">${index + 1} · ${escapeHtml(recommendation.programCode)}</p><h3>${escapeHtml(recommendation.programName)}</h3><p>${escapeHtml(topReason)}</p></div><div class="result-score"><strong>${recommendation.contentFit}</strong><span>/100 Content Fit</span><button class="secondary-button" data-result-detail="${index}" type="button">Разобрать</button></div></article>`;
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
