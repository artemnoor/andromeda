import { getPersonalRoute, type PersonalRouteResponse } from "../../api/client";
import { ApiError } from "../../api/errors";
import type { components } from "../../api/generated";

import { personalRouteNoEventsMarkup, renderPersonalRouteError, renderPersonalRouteLoading, renderPersonalRouteNoRecommendations, renderPersonalRouteProfileRequired } from "./PersonalRouteStates";

type Program = components["schemas"]["ProgramSummaryResponse"];
type Step = PersonalRouteResponse["steps"][number];

export function renderPersonalRoutePage(root: HTMLElement, programs: readonly Program[]): void {
  root.innerHTML = `<section class="hero compact personal-route-hero" data-testid="personal-route-page"><p class="eyebrow">Andromeda · персональный план</p><h1>Следующий шаг в университете</h1><p class="lead">Логическая последовательность действий по твоим рекомендациям: разобраться в программе, сопоставить варианты и увидеть подходящие события.</p></section><main id="personal-route-result" aria-live="polite"></main>`;
  const resultRoot = root.querySelector<HTMLElement>("#personal-route-result");
  if (!resultRoot) return;
  void loadPersonalRoute(resultRoot, programs);
}

async function loadPersonalRoute(root: HTMLElement, programs: readonly Program[]): Promise<void> {
  renderPersonalRouteLoading(root);
  try {
    const response = await getPersonalRoute();
    if (response.status === "no_recommendations") {
      debugFix(`rendered_status=${response.status}`);
      renderPersonalRouteNoRecommendations(root);
      return;
    }
    debugFix(`rendered_status=${response.status} step_count=${response.steps.length}`);
    root.innerHTML = renderPersonalRouteContent(response, programs);
  } catch (error: unknown) {
    if (error instanceof ApiError && error.status === 404) {
      debugFix("rendered_status=profile_required http_status=404");
      renderPersonalRouteProfileRequired(root);
      return;
    }
    const message = error instanceof ApiError ? apiErrorMessage(error) : "Не удалось получить персональный план";
    debugFix(`rendered_status=error http_status=${error instanceof ApiError ? error.status : "unknown"}`);
    renderPersonalRouteError(root, message);
  }
}

export function renderPersonalRouteContent(response: PersonalRouteResponse, programs: readonly Program[]): string {
  const steps = response.steps.map((step) => renderStep(step, programs)).join("");
  const recommendationSummary = response.recommendations.map((recommendation, index) => `<li><span>${index + 1}. ${escapeHtml(recommendation.programCode)}</span><strong>${escapeHtml(recommendation.programName)}</strong><small>Content Fit: ${recommendation.contentFit}/100</small></li>`).join("");
  const noEventsNotice = response.status === "no_events" ? personalRouteNoEventsMarkup() : "";
  return `<section class="personal-route-results" data-testid="personal-route-results"><div class="section-heading"><div><p class="eyebrow">Персональный план</p><h2>${escapeHtml(response.summary)}</h2></div><span class="status">${response.steps.length} шагов</span></div>${noEventsNotice}<section class="personal-route-recommendations"><div class="section-heading"><div><p class="eyebrow">Основа плана</p><h3>Рекомендованные программы</h3></div></div><ol>${recommendationSummary}</ol></section><div class="personal-route-steps">${steps}</div></section>`;
}

function renderStep(step: Step, programs: readonly Program[]): string {
  if (step.kind === "explore_program") return renderExploreStep(step, programs);
  if (step.kind === "compare_programs") return renderCompareStep(step, programs);
  return renderEventStep(step, programs);
}

function renderExploreStep(step: Step, programs: readonly Program[]): string {
  const recommendation = step.recommendation;
  const title = recommendation ? `${recommendation.programCode} · ${recommendation.programName}` : programLabels(step.programIds, programs);
  const score = recommendation ? `<span class="status">Content Fit ${recommendation.contentFit}/100</span>` : "";
  const programId = step.programIds[0];
  const titleMarkup = programId ? `<a class="route-step-link" href="#program/${encodeURIComponent(programId)}">${escapeHtml(title)} <span aria-hidden="true">→</span></a>` : escapeHtml(title);
  return `<article class="personal-route-step" data-testid="personal-route-step" data-step-kind="${escapeHtml(step.kind)}"><div class="personal-route-step-head"><span class="eyebrow">${String(step.position).padStart(2, "0")} · Разобраться в программе</span>${score}</div><h3>${titleMarkup}</h3><p>${escapeHtml(step.reason)}</p><code>${escapeHtml(programId ?? "")}</code></article>`;
}

function renderCompareStep(step: Step, programs: readonly Program[]): string {
  return `<article class="personal-route-step" data-testid="personal-route-step" data-step-kind="${escapeHtml(step.kind)}"><div class="personal-route-step-head"><span class="eyebrow">${String(step.position).padStart(2, "0")} · Сопоставить программы</span><span class="status">2 программы</span></div><h3>${escapeHtml(programLabels(step.programIds, programs))}</h3><p>${escapeHtml(step.reason)}</p><div class="personal-route-id-list">${step.programIds.map((id) => `<code>${escapeHtml(id)}</code>`).join("")}</div><a class="secondary-button" href="#compare">Открыть сравнение</a></article>`;
}

function renderEventStep(step: Step, programs: readonly Program[]): string {
  const event = step.event;
  if (!event) return "";
  const point = step.point ? `<div class="personal-route-point" data-testid="personal-route-point"><span class="label">Место проведения</span><strong>${escapeHtml(step.point.name)}</strong>${step.point.address ? `<span>${escapeHtml(step.point.address)}</span>` : ""}${step.point.latitude !== null && step.point.latitude !== undefined && step.point.longitude !== null && step.point.longitude !== undefined ? `<small>Координаты: ${escapeHtml(step.point.latitude)}, ${escapeHtml(step.point.longitude)}</small>` : ""}</div>` : `<div class="personal-route-point" data-testid="personal-route-point"><span class="label">Место проведения</span><strong>Онлайн или место пока не указано</strong></div>`;
  const registration = event.registrationUrl ? `<a class="secondary-button" data-testid="personal-route-registration" href="${safeHref(event.registrationUrl)}" target="_blank" rel="noreferrer">Регистрация</a>` : "";
  return `<article class="personal-route-step" data-testid="personal-route-step" data-step-kind="${escapeHtml(step.kind)}"><div class="personal-route-step-head"><span class="eyebrow">${String(step.position).padStart(2, "0")} · Посетить событие</span><span class="status">${escapeHtml(event.format)}</span></div><h3><a class="route-step-link" href="#event/${encodeURIComponent(event.id)}">${escapeHtml(event.title)} <span aria-hidden="true">→</span></a></h3><time datetime="${escapeHtml(event.startsAt)}">${escapeHtml(formatDate(event.startsAt))}</time>${event.description ? `<p>${escapeHtml(event.description)}</p>` : ""}<div class="personal-route-event-details"><div><span class="label">Связанные программы</span><p>${escapeHtml(programLabels(step.programIds, programs))}</p><code>${escapeHtml(event.id)}</code></div>${point}</div><div class="personal-route-step-actions"><a class="secondary-button" href="#event/${encodeURIComponent(event.id)}">Открыть событие</a>${registration}</div></article>`;
}

function programLabels(ids: readonly string[], programs: readonly Program[]): string {
  return ids.map((id) => {
    const program = programs.find((item) => item.id === id);
    return program ? `${program.code} · ${program.name}` : id;
  }).join(" · ");
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ru-RU", { dateStyle: "long", timeStyle: "short" }).format(date);
}

function safeHref(value: string): string {
  try {
    const base = typeof window === "undefined" ? "http://localhost/" : window.location.origin;
    const url = new URL(value, base);
    return url.protocol === "http:" || url.protocol === "https:" ? escapeHtml(url.href) : "#";
  } catch {
    return "#";
  }
}

function apiErrorMessage(error: ApiError): string {
  if (error.status >= 500) return "Сервис персональных планов временно недоступен";
  if (error.status === 400 || error.status === 422) return "Не удалось проверить параметры запроса персонального плана";
  return "Не удалось получить персональный план";
}

function debugFix(message: string): void {
  if (import.meta.env.DEV && import.meta.env.VITE_LOG_LEVEL === "DEBUG") console.debug(`[FIX:personal-route] ${message}`);
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
