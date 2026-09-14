import { getCurrentProfile, getCurrentRecommendations, getEvents } from "../../api/client";
import { ApiError } from "../../api/errors";

export type FlowStageId = "catalog" | "compare" | "profile" | "recommendations" | "program" | "admission-fit" | "events" | "personal-route";
export type UnifiedReadStatus = "ready" | "profile-required" | "empty" | "error";
export type UnifiedStageStatus = "available" | "ready" | "profile-required" | "empty" | "error";

export type UnifiedReadModel = {
  profile: Readonly<{ status: UnifiedReadStatus }>;
  recommendations: Readonly<{
    status: UnifiedReadStatus;
    count: number;
    firstProgramId?: string;
  }>;
  events: Readonly<{
    status: UnifiedReadStatus;
    count: number;
  }>;
};

export type UnifiedMvpStage = Readonly<{
  id: FlowStageId;
  title: string;
  description: string;
  href: string;
  status: UnifiedStageStatus;
}>;

type ProfileResult = Awaited<ReturnType<typeof getCurrentProfile>>;
type RecommendationsResult = Awaited<ReturnType<typeof getCurrentRecommendations>>;

export async function loadUnifiedMvpState(): Promise<UnifiedReadModel> {
  debug("read_start");
  const [profileResult, recommendationsResult] = await Promise.allSettled([getCurrentProfile(), getCurrentRecommendations()]);
  const profile = profileState(profileResult);
  const recommendations = recommendationState(recommendationsResult);
  const events = profile.status === "ready" ? await readRecommendedEvents() : { status: profile.status, count: 0 };
  debug(`read_complete profile=${profile.status} recommendations=${recommendations.status} events=${events.status}`);
  return { profile, recommendations, events };
}

export function deriveUnifiedMvpStages(model: UnifiedReadModel): readonly UnifiedMvpStage[] {
  const programHref = model.recommendations.firstProgramId
    ? `#program/${encodeURIComponent(model.recommendations.firstProgramId)}`
    : "#program";
  const recommendationStatus = model.recommendations.status === "ready" ? "ready" : model.recommendations.status;
  const programStatus: UnifiedStageStatus = model.recommendations.firstProgramId ? "ready" : "available";
  const personalRouteStatus: UnifiedStageStatus = model.profile.status === "profile-required"
    ? "profile-required"
    : model.recommendations.status === "empty"
      ? "empty"
      : model.recommendations.status === "error"
        ? "error"
        : "available";

  return [
    { id: "catalog", title: "Найти программу", description: "Открой каталог программ и начни с подходящего направления.", href: "#program", status: "available" },
    { id: "compare", title: "Сравнить варианты", description: "Сопоставь две программы по учебному плану и ключевым блокам.", href: "#compare", status: "available" },
    { id: "profile", title: "Пройти профтест", description: "Сохрани профиль интересов, чтобы получить персональные рекомендации.", href: "#proftest", status: model.profile.status === "ready" ? "ready" : model.profile.status },
    { id: "recommendations", title: "Посмотреть рекомендации", description: "Результаты и объяснения рекомендаций находятся в профтесте.", href: "#proftest", status: recommendationStatus },
    { id: "program", title: "Изучить рекомендованную программу", description: "Перейди к карточке первой доступной рекомендации.", href: programHref, status: programStatus },
    { id: "admission-fit", title: "Проверить Admission Fit", description: "В карточке программы доступны admissions и расчёт Admission Fit.", href: programHref, status: programStatus },
    { id: "events", title: "Выбрать событие", description: "На странице событий включи существующий фильтр «Для меня».", href: "#events", status: model.events.status },
    { id: "personal-route", title: "Открыть Personal Route", description: "Собери логический план следующих шагов без маршрутизации по карте.", href: "#personal-route", status: personalRouteStatus },
  ];
}

async function readRecommendedEvents(): Promise<Readonly<{ status: UnifiedReadStatus; count: number }>> {
  try {
    const response = await getEvents({ recommended: true, limit: 4 });
    return response.items.length > 0 ? { status: "ready", count: response.items.length } : { status: "empty", count: 0 };
  } catch (error: unknown) {
    warnForReadError("events", error);
    return { status: classifyError(error), count: 0 };
  }
}

function profileState(result: PromiseSettledResult<ProfileResult>): Readonly<{ status: UnifiedReadStatus }> {
  if (result.status === "fulfilled") return { status: "ready" };
  warnForReadError("current_profile", result.reason);
  return { status: classifyError(result.reason) };
}

function recommendationState(result: PromiseSettledResult<RecommendationsResult>): Readonly<{ status: UnifiedReadStatus; count: number; firstProgramId?: string }> {
  if (result.status === "rejected") {
    warnForReadError("recommendations", result.reason);
    return { status: classifyError(result.reason), count: 0 };
  }
  const response = result.value;
  const count = response.recommendations.length;
  if (count === 0) return { status: "empty", count: 0 };
  const firstProgramId = response.recommendations[0]?.programId;
  return firstProgramId ? { status: "ready", count, firstProgramId } : { status: "ready", count };
}

function classifyError(error: unknown): "profile-required" | "error" {
  return error instanceof ApiError && error.status === 404 ? "profile-required" : "error";
}

function warnForReadError(read: string, error: unknown): void {
  const status = error instanceof ApiError ? error.status : "unknown";
  console.warn(`[unified-flow] ${read}_read_error status=${status}`);
}

function debug(message: string): void {
  if (import.meta.env.DEV && import.meta.env.VITE_LOG_LEVEL === "DEBUG") console.debug(`[unified-flow] ${message}`);
}
