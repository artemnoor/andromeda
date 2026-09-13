import type { components } from "../../api/generated";

import { loadUnifiedMvpState, deriveUnifiedMvpStages, type UnifiedMvpStage, type UnifiedReadModel, type UnifiedStageStatus } from "./unifiedMvpState";

type Program = components["schemas"]["ProgramSummaryResponse"];

export function renderUnifiedMvpPage(root: HTMLElement, programs: readonly Program[]): void {
  root.innerHTML = `<section class="hero compact unified-flow-hero"><p class="eyebrow">Andromeda · единый путь</p><h1>От интереса к следующему шагу</h1><p class="lead">Собери свой путь по существующим разделам: программа, профиль, рекомендации, события и Personal Route.</p></section><main id="unified-flow-content" aria-live="polite"><section class="state-card unified-flow-state" data-testid="unified-flow-loading" role="status"><p class="eyebrow">Unified MVP Flow</p><h2>Проверяем готовность пути</h2><p>Загружаем профиль, рекомендации и подходящие события.</p></section></main>`;
  const contentRoot = root.querySelector<HTMLElement>("#unified-flow-content");
  if (!contentRoot) return;
  void loadUnifiedMvpState()
    .then((model) => {
      contentRoot.innerHTML = renderUnifiedMvpMarkup(model, programs);
    })
    .catch(() => {
      console.warn("[unified-flow] read_error");
      contentRoot.innerHTML = renderUnifiedMvpError();
    });
}

export function renderUnifiedMvpMarkup(model: UnifiedReadModel, programs: readonly Program[]): string {
  const stages = deriveUnifiedMvpStages(model);
  const recommendedProgram = model.recommendations.firstProgramId ? programs.find((program) => program.id === model.recommendations.firstProgramId) : undefined;
  const recommendationLabel = recommendedProgram ? `${recommendedProgram.code} · ${recommendedProgram.name}` : model.recommendations.firstProgramId;
  const stageMarkup = stages.map((stage, index) => renderStage(stage, index, recommendationLabel)).join("");

  return `<section class="unified-flow-results" data-testid="unified-flow-page"><div class="section-heading unified-flow-heading"><div><p class="eyebrow">Путь пользователя</p><h2>Следующий шаг уже рядом</h2><p class="muted">Каждая карточка открывает существующий раздел Andromeda и сохраняет его собственные данные и состояния.</p></div><span class="status" data-testid="unified-flow-stage-count">${stages.length} этапов</span></div><section class="unified-flow-readiness" aria-label="Готовность данных"><article class="unified-flow-readiness-card" data-testid="unified-flow-profile-status"><span class="label">Профиль</span><strong>${escapeHtml(readinessLabel(model.profile.status))}</strong><small>${model.profile.status === "ready" ? "Профиль интересов сохранён." : "Пройди профтест для персонального пути."}</small></article><article class="unified-flow-readiness-card" data-testid="unified-flow-recommendations-status"><span class="label">Рекомендации</span><strong>${escapeHtml(readinessLabel(model.recommendations.status))}</strong><small>${escapeHtml(readinessDetail(model.recommendations.status, model.recommendations.count, "рекомендаций"))}</small></article><article class="unified-flow-readiness-card" data-testid="unified-flow-events-status"><span class="label">События</span><strong>${escapeHtml(readinessLabel(model.events.status))}</strong><small>${escapeHtml(readinessDetail(model.events.status, model.events.count, "событий"))}</small></article></section>${model.profile.status === "profile-required" ? `<p class="unified-flow-notice" data-testid="unified-flow-profile-required">Чтобы открыть персональные этапы, сначала сохрани профиль в профтесте. <a href="#proftest">Открыть профтест</a></p>` : ""}${hasReadError(model) ? `<p class="unified-flow-notice unified-flow-notice-error" data-testid="unified-flow-read-warning" role="status">Часть персональных данных временно недоступна. Доступные разделы пути остаются открыты.</p>` : ""}<ol class="unified-flow-stages" aria-label="Этапы пути">${stageMarkup}</ol></section>`;
}

function renderStage(stage: UnifiedMvpStage, index: number, recommendationLabel: string | undefined): string {
  const programDetail = (stage.id === "program" || stage.id === "admission-fit") && recommendationLabel
    ? `<code class="unified-flow-program-id">${escapeHtml(recommendationLabel)}</code>`
    : "";
  const status = statusClass(stage.status);
  return `<li class="unified-flow-stage unified-flow-stage-${status}" data-testid="unified-flow-stage" data-stage-id="${escapeHtml(stage.id)}"><div class="unified-flow-stage-number">${String(index + 1).padStart(2, "0")}</div><div class="unified-flow-stage-body"><div class="unified-flow-stage-topline"><span class="eyebrow">${escapeHtml(stageLabel(stage.id))}</span><span class="status" data-testid="unified-flow-status">${escapeHtml(readinessLabel(stage.status))}</span></div><h3>${escapeHtml(stage.title)}</h3><p>${escapeHtml(stage.description)}</p>${programDetail}<a class="secondary-button unified-flow-cta" data-testid="unified-flow-cta" href="${escapeHtml(stage.href)}">${escapeHtml(ctaLabel(stage.id))}</a></div></li>`;
}

function renderUnifiedMvpError(): string {
  return `<section class="state-card unified-flow-state error-state" data-testid="unified-flow-error" role="alert"><p class="eyebrow">Unified MVP Flow</p><h2>Не удалось проверить готовность пути</h2><p>Перейди в доступный раздел и повтори попытку позже.</p><div class="unified-flow-error-links"><a class="primary-button" href="#proftest">Открыть профтест</a><a class="secondary-button" href="#events">Открыть события</a><a class="secondary-button" href="#personal-route">Открыть Personal Route</a></div></section>`;
}

function stageLabel(id: UnifiedMvpStage["id"]): string {
  const labels: Record<UnifiedMvpStage["id"], string> = {
    catalog: "Каталог",
    compare: "Сравнение",
    profile: "Профиль",
    recommendations: "Рекомендации",
    program: "Программа",
    "admission-fit": "Admission Fit",
    events: "События",
    "personal-route": "Personal Route",
  };
  return labels[id];
}

function ctaLabel(id: UnifiedMvpStage["id"]): string {
  if (id === "profile") return "Пройти профтест";
  if (id === "recommendations") return "Открыть рекомендации";
  if (id === "program") return "Открыть программу";
  if (id === "admission-fit") return "Проверить в программе";
  if (id === "events") return "Открыть события";
  if (id === "personal-route") return "Открыть план";
  if (id === "compare") return "Сравнить программы";
  return "Открыть каталог";
}

function readinessLabel(status: UnifiedReadModel["profile"]["status"] | UnifiedStageStatus): string {
  if (status === "ready") return "Готово";
  if (status === "profile-required") return "Нужен профиль";
  if (status === "empty") return "Пока пусто";
  if (status === "error") return "Не удалось проверить";
  return "Доступно";
}

function readinessDetail(status: UnifiedReadStatusLike, count: number, noun: string): string {
  if (status === "ready") return `${count} ${noun} доступны.`;
  if (status === "empty") return "Пока нет данных для этого этапа.";
  if (status === "profile-required") return "Станет доступно после сохранения профиля.";
  return "Попробуй открыть раздел напрямую.";
}

function statusClass(status: UnifiedStageStatus): string {
  return status === "profile-required" ? "profile-required" : status;
}

function hasReadError(model: UnifiedReadModel): boolean {
  return model.profile.status === "error" || model.recommendations.status === "error" || model.events.status === "error";
}

type UnifiedReadStatusLike = UnifiedReadModel["profile"]["status"];

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
