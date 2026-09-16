import { getCurrentProfile, getCurrentRecommendations } from "../../api/client";
import { ApiError } from "../../api/errors";
import type { components } from "../../api/generated";
import { areaLabel } from "../proftest/taxonomyLabels";

type Recommendation = components["schemas"]["RecommendationResponse"];

export function renderRecommendationsPage(root: HTMLElement): void {
  root.innerHTML = `<section class="hero recommendations-hero" data-testid="recommendations-page"><div class="hero-kicker"><span class="eyebrow">Andromeda · рекомендации</span><span class="hero-index">05 / 10</span></div><h1>Не просто «подходит» — вот почему.</h1><p class="lead">Content Fit связывает твой профиль с тем, что реально изучают на программе. Открой причины, анти-fit сигналы и учебные области перед следующим шагом.</p><div class="hero-actions"><a class="primary-button" href="#proftest">Изменить профиль</a><a class="text-link" href="#catalog">Вернуться в каталог <span aria-hidden="true">→</span></a></div></section><main id="recommendations-content" aria-live="polite"><section class="state-card recommendations-loading" data-testid="recommendations-loading" role="status"><p class="eyebrow">Content Fit</p><h2>Собираем актуальные рекомендации…</h2><p>Запрашиваем сохранённый профиль и сравнение с учебными планами.</p></section></main>`;
  const content = root.querySelector<HTMLElement>("#recommendations-content");
  if (!content) return;
  void Promise.all([getCurrentProfile(), getCurrentRecommendations()])
    .then(([profile, response]) => {
      if (response.recommendations.length === 0) {
        content.innerHTML = `<section class="state-card recommendations-empty" data-testid="recommendations-empty"><p class="eyebrow">Content Fit</p><h2>Рекомендаций пока нет</h2><p>Пройди профтест ещё раз, когда захочешь обновить сигналы, или начни с каталога.</p><div class="hero-actions"><a class="primary-button" href="#proftest">Пройти профтест</a><a class="secondary-button" href="#catalog">Открыть каталог</a></div></section>`;
        return;
      }
      content.innerHTML = renderRecommendations(response.recommendations, profile.profile.interests);
    })
    .catch((error: unknown) => {
      const profileRequired = error instanceof ApiError && error.status === 404;
      content.innerHTML = profileRequired
        ? `<section class="state-card recommendations-profile-required" data-testid="recommendations-profile-required"><p class="eyebrow">Сначала профиль</p><h2>Чтобы получить рекомендации, ответь на несколько вопросов.</h2><p>Профиль нужен, чтобы объяснить не только совпадение, но и то, что может не подойти.</p><a class="primary-button" data-testid="recommendations-profile-link" href="#proftest">Открыть профтест</a></section>`
        : `<section class="state-card error-state" data-testid="recommendations-error" role="alert"><p class="eyebrow">Ошибка API</p><h2>Не удалось загрузить рекомендации</h2><p>${escapeHtml(error instanceof ApiError ? error.payload.message : "Проверь соединение с backend и повтори попытку.")}</p><button class="secondary-button" data-testid="recommendations-retry" type="button">Повторить</button></section>`;
      content.querySelector<HTMLButtonElement>("[data-testid='recommendations-retry']")?.addEventListener("click", () => renderRecommendationsPage(root));
    });
}

function renderRecommendations(recommendations: readonly Recommendation[], interests: readonly string[]): string {
  return `<section class="recommendations-results" data-testid="recommendations-results"><div class="section-heading recommendations-heading"><div><p class="eyebrow">Твой профиль содержания</p><h2>TOP программ</h2><p class="muted">Рейтинг построен по структуре учебного плана и доступным сигналам профиля.</p></div><span class="status">${recommendations.length} результатов</span></div><div class="profile-pills">${interests.slice(0, 5).map((interest) => `<span>${escapeHtml(areaLabel(interest))}</span>`).join("")}</div><div class="recommendations-grid">${recommendations.map(renderRecommendationCard).join("")}</div></section>`;
}

function renderRecommendationCard(recommendation: Recommendation, index: number): string {
  const positive = recommendation.reasons.slice(0, 3).map((reason) => reasonLine(reason.text, "positive")).join("") || `<p class="muted">Явных положительных сигналов пока нет.</p>`;
  const negative = recommendation.antiFitReasons.slice(0, 3).map((reason) => reasonLine(reason.text, "negative")).join("") || `<p class="muted">Сильных anti-interest конфликтов не найдено.</p>`;
  return `<article class="recommendation-card" data-testid="recommendation-card"><div class="recommendation-card-header"><div><span class="eyebrow">${String(index + 1).padStart(2, "0")} · ${escapeHtml(recommendation.programCode)}</span><h3>${escapeHtml(recommendation.programName)}</h3></div><div class="recommendation-score"><strong>${recommendation.contentFit}</strong><span>/100</span></div></div><div class="recommendation-meter" aria-label="Content Fit ${recommendation.contentFit} из 100"><i style="width:${Math.max(0, Math.min(100, recommendation.contentFit))}%"></i></div><div class="recommendation-reasons"><section><h4>Подходит</h4>${positive}</section><section><h4>Может не подойти</h4>${negative}</section></div><div class="recommendation-card-footer"><a class="primary-button" data-testid="recommendation-program-link" href="#program/${encodeURIComponent(recommendation.programId)}">Открыть программу</a><span class="muted">Content Fit · учебный план</span></div></article>`;
}

function reasonLine(text: string, kind: "positive" | "negative"): string {
  return `<p class="recommendation-reason recommendation-reason-${kind}"><b aria-hidden="true">${kind === "positive" ? "+" : "−"}</b><span>${escapeHtml(text)}</span></p>`;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
