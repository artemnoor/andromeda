import { getAuthSession, getCurrentProfile, getCurrentRecommendations, getPersonalRoute, type AuthSessionResponse, type CurrentProfileResponse, type CurrentRecommendationsResponse, type PersonalRouteResponse } from "../../api/client";
import { ApiError } from "../../api/errors";
import { areaLabel } from "../proftest/taxonomyLabels";

export function renderAccountPage(root: HTMLElement): void {
  root.innerHTML = `<section class="hero account-hero" data-testid="account-page"><div class="hero-kicker"><span class="eyebrow">Andromeda · личный кабинет</span><span class="hero-index">09 / 10</span></div><h1>Твой прогресс — в одном месте.</h1><p class="lead">Сохраняй профиль, возвращайся к рекомендациям и продолжай Personal Route с того шага, на котором остановился.</p></section><main id="account-content" aria-live="polite"><section class="state-card" data-testid="account-loading" role="status"><p class="eyebrow">Личный кабинет</p><h2>Проверяем сохранённые данные…</h2><p>Загружаем аккаунт, профиль, рекомендации и план.</p></section></main>`;
  const content = root.querySelector<HTMLElement>("#account-content");
  if (!content) return;
  void Promise.allSettled([getAuthSession(), getCurrentProfile(), getCurrentRecommendations(), getPersonalRoute()]).then(([session, profile, recommendations, route]) => {
    content.innerHTML = renderAccountContent(session, profile, recommendations, route);
  });
}

function renderAccountContent(
  session: PromiseSettledResult<AuthSessionResponse>,
  profile: PromiseSettledResult<CurrentProfileResponse>,
  recommendations: PromiseSettledResult<CurrentRecommendationsResponse>,
  route: PromiseSettledResult<PersonalRouteResponse>,
): string {
  const sessionData = fulfilled(session) ? session.value : null;
  const profileData = fulfilled(profile) ? profile.value : null;
  const recommendationData = fulfilled(recommendations) ? recommendations.value : null;
  const routeData = fulfilled(route) ? route.value : null;
  const accountLabel = sessionData?.authenticated && sessionData.account ? escapeHtml(sessionData.account.email) : "Гостевой режим";
  const profileMissing = isNotFound(profile) || !profileData;
  const recommendationsMissing = isNotFound(recommendations) || !recommendationData;
  const routeMissing = isNotFound(route) || !routeData;

  return `<section class="account-overview"><article class="account-identity"><span class="label">Сессия</span><strong data-testid="account-identity">${accountLabel}</strong><p>${sessionData?.authenticated ? "Профиль привязан к аккаунту и восстановится после входа." : "Войди через панель сверху, чтобы привязать профиль к аккаунту."}</p>${!sessionData?.authenticated ? `<a class="text-link" href="#catalog">Продолжить как гость <span aria-hidden="true">→</span></a>` : ""}</article><article class="account-stat"><span class="label">Профиль</span><strong>${profileData ? "Сохранён" : "Нужен профтест"}</strong><span>${profileData ? `Обновлён ${formatDate(profileData.updatedAt)}` : "6 коротких вопросов"}</span></article><article class="account-stat"><span class="label">Рекомендации</span><strong>${recommendationData?.recommendations.length ?? "—"}</strong><span>${recommendationsMissing ? "После профиля" : "Content Fit программ"}</span></article><article class="account-stat"><span class="label">Personal Route</span><strong>${routeData?.steps.length ?? "—"}</strong><span>${routeMissing ? "После профиля" : "логических шагов"}</span></article></section>${profileMissing ? `<section class="account-section account-profile-required" data-testid="account-profile"><div><p class="eyebrow">Сохранённый профиль</p><h2>Начни с того, что тебе интересно.</h2><p class="muted">Мы не угадываем профессию — сопоставляем интересы с реальными дисциплинами.</p></div><a class="primary-button" data-testid="account-proftest-link" href="#proftest">Пройти профтест</a></section>` : renderProfile(profileData)}${recommendationData ? renderRecommendations(recommendationData) : `<section class="account-section" data-testid="account-recommendations"><div><p class="eyebrow">Рекомендации</p><h2>Они появятся после профиля.</h2></div><a class="secondary-button" href="#recommendations">Открыть раздел</a></section>`}${routeData ? renderRoute(routeData) : `<section class="account-section" data-testid="account-route"><div><p class="eyebrow">Personal Route</p><h2>План соберётся из твоих следующих шагов.</h2><p class="muted">После рекомендаций можно перейти к программе, сравнению и подходящему событию.</p></div><a class="secondary-button" href="#personal-route">Открыть план</a></section>`}`;
}

function renderProfile(profile: CurrentProfileResponse): string {
  return `<section class="account-section" data-testid="account-profile"><div class="section-heading"><div><p class="eyebrow">Сохранённый профиль</p><h2>Что тебе интересно</h2></div><span class="status">Ревизия ${profile.revision}</span></div><div class="profile-pills">${profile.profile.interests.map((interest) => `<span>${escapeHtml(areaLabel(interest))}</span>`).join("") || `<span>Интересы ещё уточняются</span>`}</div><p class="muted">Профиль обновлён ${escapeHtml(formatDate(profile.updatedAt))}. Можно изменить ответы в профориентационном тесте.</p><a class="text-link" href="#proftest">Изменить профиль <span aria-hidden="true">→</span></a></section>`;
}

function renderRecommendations(response: CurrentRecommendationsResponse): string {
  const cards = response.recommendations.slice(0, 3).map((recommendation, index) => `<li><span>${String(index + 1).padStart(2, "0")}</span><div><strong>${escapeHtml(recommendation.programName)}</strong><small>${escapeHtml(recommendation.programCode)} · ${recommendation.contentFit}/100 Content Fit</small></div><a class="text-link" href="#program/${encodeURIComponent(recommendation.programId)}">Открыть</a></li>`).join("");
  return `<section class="account-section" data-testid="account-recommendations"><div class="section-heading"><div><p class="eyebrow">Последние рекомендации</p><h2>С чего начать</h2></div><a class="text-link" href="#recommendations">Все рекомендации <span aria-hidden="true">→</span></a></div><ol class="account-list">${cards || `<li><span>—</span><div><strong>Пока нет рекомендаций</strong><small>Пройди профтест, чтобы увидеть Content Fit.</small></div></li>`}</ol></section>`;
}

function renderRoute(response: PersonalRouteResponse): string {
  return `<section class="account-section" data-testid="account-route"><div class="section-heading"><div><p class="eyebrow">Personal Route</p><h2>${escapeHtml(response.summary)}</h2></div><a class="text-link" href="#personal-route">Открыть план <span aria-hidden="true">→</span></a></div><p class="muted">${response.steps.length} шагов · статус: ${escapeHtml(routeStatusLabel(response.status))}</p></section>`;
}

function routeStatusLabel(status: PersonalRouteResponse["status"]): string {
  if (status === "ready") return "готов";
  if (status === "no_events") return "без событий";
  return "нет рекомендаций";
}

function fulfilled<T>(result: PromiseSettledResult<T>): result is PromiseFulfilledResult<T> {
  return result.status === "fulfilled";
}

function isNotFound(result: PromiseSettledResult<unknown>): boolean {
  return result.status === "rejected" && result.reason instanceof ApiError && result.reason.status === 404;
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : new Intl.DateTimeFormat("ru-RU", { dateStyle: "medium" }).format(date);
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
