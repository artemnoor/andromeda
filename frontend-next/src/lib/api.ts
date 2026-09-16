/*
 * Live adapter for the attached Next.js UI.
 *
 * The backend remains the source of truth.  This module only translates the
 * generated FastAPI contract into the view-models used by the imported UI;
 * there are no catalogue, admissions, profile, or event fixtures in this path.
 */

import type { components, paths } from "./generated";
import type {
  AccountInfo,
  AdmissionFitRequest,
  AdmissionFitResponse,
  AdmissionOffering,
  AuthSession,
  CampusPoint,
  CampusPointDetailResponse,
  CampusPointEventsResponse,
  CampusRecommendationsResponse,
  ComparisonResponse,
  CurriculumResponse,
  Discipline,
  DisciplineArea,
  EventDetailResponse,
  EventItem,
  EventListResponse,
  IngestionRetryRequest,
  IngestionRunDetail,
  IngestionRunDetailResponse,
  IngestionRunListResponse,
  IngestionRunStatus,
  IngestionRunSummary,
  PersonalRouteResponse,
  PersonalRouteStep,
  ProgramAdmissionsResponse,
  ProgramListResponse,
  ProgramResponse,
  ProftestPreviewResponse,
  ProftestSessionAnswerRequest,
  ProftestSessionResponse,
  ProftestResultsResponse,
  ProftestSubmissionRequest,
  QuestionnaireResponse,
  Recommendation,
  RecommendationsResponse,
  UserProfile,
  UserProfileSnapshot,
} from "./types";

type ApiProgramList = paths["/programs"]["get"]["responses"][200]["content"]["application/json"];
type ApiProgram = paths["/programs/{id}"]["get"]["responses"][200]["content"]["application/json"];
type ApiCurriculum = paths["/programs/{id}/curriculum"]["get"]["responses"][200]["content"]["application/json"];
type ApiAdmissions = paths["/programs/{id}/admissions"]["get"]["responses"][200]["content"]["application/json"];
type ApiAdmissionFit = paths["/programs/{id}/admission-fit"]["post"]["responses"][200]["content"]["application/json"];
type ApiComparison = paths["/compare"]["get"]["responses"][200]["content"]["application/json"];
type ApiQuestions = paths["/proftest/questions"]["get"]["responses"][200]["content"]["application/json"];
type ApiPreview = paths["/proftest/preview"]["post"]["responses"][200]["content"]["application/json"];
type ApiResults = paths["/proftest/results"]["post"]["responses"][200]["content"]["application/json"];
type ApiProftestSession = paths["/proftest/sessions"]["post"]["responses"][200]["content"]["application/json"];
type ApiProftestSessionAnswer = components["schemas"]["ProftestSessionAnswerRequest"];
type ApiProftestSessionPatch = NonNullable<paths["/proftest/sessions/current"]["patch"]["requestBody"]>["content"]["application/json"];
type ApiProftestSessionNext = NonNullable<paths["/proftest/sessions/current/next"]["post"]["requestBody"]>["content"]["application/json"];
type ApiProftestAnalytics = NonNullable<paths["/proftest/analytics"]["post"]["requestBody"]>["content"]["application/json"];
type ApiProfile = paths["/proftest/profile"]["get"]["responses"][200]["content"]["application/json"];
type ApiRecommendations = paths["/recommendations/current"]["get"]["responses"][200]["content"]["application/json"];
type ApiEvents = paths["/events"]["get"]["responses"][200]["content"]["application/json"];
type ApiEvent = paths["/events/{id}"]["get"]["responses"][200]["content"]["application/json"];
type ApiPoint = paths["/campus/points/{id}"]["get"]["responses"][200]["content"]["application/json"];
type ApiPointEvents = paths["/campus/points/{id}/events"]["get"]["responses"][200]["content"]["application/json"];
type ApiCampusRecommendations = paths["/campus/recommendations"]["get"]["responses"][200]["content"]["application/json"];
type ApiRoute = paths["/personal-route"]["get"]["responses"][200]["content"]["application/json"];
type ApiRuns = paths["/ops/ingestion/runs"]["get"]["responses"][200]["content"]["application/json"];
type ApiRun = paths["/ops/ingestion/runs/{id}"]["get"]["responses"][200]["content"]["application/json"];
type ApiRetry = paths["/ops/ingestion/runs/retry"]["post"]["responses"][200]["content"]["application/json"];
type ApiSession = paths["/auth/session"]["get"]["responses"][200]["content"]["application/json"];

const CONFIGURED_API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api").replace(/\/$/, "");
const DEBUG_API_REQUESTS = process.env.NEXT_PUBLIC_DEBUG_API === "1";
export const API_REQUEST_TIMEOUT_MS = 45_000;

function getApiBaseUrl(): string {
  if (typeof window === "undefined") return CONFIGURED_API_BASE_URL;
  try {
    const url = new URL(CONFIGURED_API_BASE_URL);
    const localHosts = new Set(["localhost", "127.0.0.1"]);
    if (localHosts.has(url.hostname) && localHosts.has(window.location.hostname)) {
      url.hostname = window.location.hostname;
    }
    return url.toString().replace(/\/$/, "");
  } catch {
    return CONFIGURED_API_BASE_URL;
  }
}

export class ApiRequestError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "ApiRequestError";
  }
}

async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timeout = globalThis.setTimeout(() => controller.abort(), API_REQUEST_TIMEOUT_MS);
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body !== undefined) headers.set("Content-Type", "application/json");
  const apiBaseUrl = getApiBaseUrl();

  if (DEBUG_API_REQUESTS) {
    console.debug("[FIX:catalog-api] request", { path, apiBaseUrl });
  }

  try {
    const response = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      credentials: "include",
      cache: "no-store",
      headers,
      signal: init.signal ?? controller.signal,
    });
    if (DEBUG_API_REQUESTS) {
      console.debug("[FIX:catalog-api] response", { path, status: response.status });
    }
    const text = await response.text();
    let payload: unknown = null;
    try {
      payload = text ? JSON.parse(text) : null;
    } catch {
      payload = text;
    }
    if (!response.ok) {
      const message = typeof payload === "object" && payload !== null && "message" in payload
        ? String((payload as { message: unknown }).message)
        : `API request failed with ${response.status}`;
      throw new ApiRequestError(response.status, message);
    }
    return payload as T;
  } catch (error) {
    if (DEBUG_API_REQUESTS) {
      console.error("[FIX:catalog-api] request_failed", {
        path,
        message: error instanceof Error ? error.message : "unknown error",
      });
    }
    throw error;
  } finally {
    globalThis.clearTimeout(timeout);
  }
}

function record(value: unknown): Record<string, any> {
  return value !== null && typeof value === "object" ? value as Record<string, any> : {};
}

function numberOrNull(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function mapProvenance(value: unknown): Record<string, any> {
  const raw = record(value);
  return {
    sourceKind: raw.sourceKind ?? raw.kind ?? null,
    sourceUrl: raw.sourceUrl ?? raw.url ?? null,
    capturedAt: raw.capturedAt ?? null,
    contentSha256: raw.contentSha256 ?? null,
    locator: raw.locator ?? null,
    sourceName: raw.sourceName ?? null,
  };
}

function mapProgram(raw: any) {
  return {
    id: raw.id,
    directionId: raw.directionId,
    code: raw.code,
    name: raw.name,
    educationYear: String(raw.educationYear),
    studyPlanUrl: raw.studyPlanUrl ?? null,
    sourceUrl: raw.sourceUrl ?? null,
  };
}

function mapDiscipline(raw: any): Discipline {
  return {
    id: raw.id,
    name: raw.name,
    normalizedName: raw.normalizedName,
    primaryArea: raw.primaryArea,
    areaWeights: (raw.areaWeights ?? []).map((area: any): DisciplineArea => ({
      code: area.code,
      name: area.name,
      description: area.description ?? null,
      weight: String(area.weight),
    })),
  };
}

function mapCurriculum(raw: any): CurriculumResponse {
  return {
    program: mapProgram(raw.program),
    curriculumId: raw.curriculumId,
    educationYear: String(raw.educationYear),
    sourceUrl: raw.sourceUrl ?? null,
    capturedAt: raw.capturedAt,
    items: (raw.items ?? []).map((item: any) => ({
      id: item.id,
      discipline: mapDiscipline(item.discipline),
      sourceName: item.sourceName,
      hours: item.hours,
      semester: item.semester ?? null,
      credits: item.credits ?? null,
      assessmentTypes: item.assessmentTypes ?? null,
      sourcePosition: item.sourcePosition ?? null,
    })),
  };
}

function mapAdmissions(raw: any): ProgramAdmissionsResponse {
  const offerings: AdmissionOffering[] = (raw.offerings ?? []).map((offering: any) => ({
    id: offering.id,
    admissionYear: offering.admissionYear,
    studyForm: offering.studyForm ?? "unknown",
    fundingType: offering.fundingType ?? "unknown",
    scope: offering.scope,
    places: offering.places ?? null,
    exams: (offering.exams ?? []).map((exam: any) => ({
      subject: exam.subject,
      sourceName: exam.sourceName ?? null,
      minimumScore: numberOrNull(exam.minimumScore),
      isChoice: exam.isChoice ?? false,
      isRequired: exam.isRequired ?? true,
      provenance: mapProvenance(exam.provenance),
    })),
    quotas: (offering.quotas ?? []).map((quota: any) => ({
      quotaType: quota.quotaType,
      sourceName: quota.sourceName ?? null,
      places: quota.places ?? null,
      provenance: mapProvenance(quota.provenance),
    })),
    passingScores: (offering.passingScores ?? []).map((passing: any) => ({
      scoreType: passing.scoreType,
      competitionType: passing.competitionType,
      status: passing.status,
      score: passing.score ?? null,
      provenance: mapProvenance(passing.provenance),
    })),
    tuition: (offering.tuition ?? []).map((tuition: any) => ({
      amount: tuition.amount,
      currency: tuition.currency,
      academicYear: tuition.academicYear ?? null,
      period: tuition.period ?? null,
      studyForm: tuition.studyForm ?? null,
      isDiscounted: tuition.isDiscounted ?? false,
      provenance: mapProvenance(tuition.provenance),
    })),
    provenance: (offering.provenance ?? []).map(mapProvenance),
  }));
  return { program: mapProgram(raw.program), programId: raw.programId, offerings };
}

function mapAdmissionFit(raw: any): AdmissionFitResponse {
  const metric = (value: unknown) => numberOrNull(record(value).value);
  const reason = (value: any) => {
    const item = record(value);
    return item.message ?? "Недостаточно данных для пояснения.";
  };
  return {
    status: raw.status,
    score: raw.score,
    applicantTotalScore: raw.applicantTotalScore ?? null,
    dataQuality: raw.dataQuality,
    breakdown: {
      minimumReadiness: metric(raw.breakdown?.minimumReadiness),
      passingReadiness: metric(raw.breakdown?.passingReadiness),
      dataCompleteness: metric(raw.breakdown?.dataCompleteness),
    },
    reasons: (raw.reasons ?? []).map(reason),
    antiReasons: (raw.antiReasons ?? []).map(reason),
    dataGaps: (raw.dataGaps ?? []).map(reason),
  };
}

function mapComparison(raw: any): ComparisonResponse {
  return {
    programA: mapProgram(raw.programA),
    programB: mapProgram(raw.programB),
    scope: raw.scope,
    semester: raw.semester ?? null,
    rows: (raw.rows ?? []).map((row: any) => ({
      discipline: row.discipline?.name ?? "Без названия",
      semester: row.semester ?? null,
      hoursA: row.a?.hours ?? null,
      hoursB: row.b?.hours ?? null,
      creditsA: row.a?.credits ?? null,
      creditsB: row.b?.credits ?? null,
      presentA: row.a != null,
      presentB: row.b != null,
      deltaHours: row.hoursDelta ?? null,
      deltaCredits: row.creditsDelta ?? null,
    })),
    totalsA: { totalHours: raw.totalsA?.hours ?? 0, totalCredits: raw.totalsA?.credits ?? "0.0000" },
    totalsB: { totalHours: raw.totalsB?.hours ?? 0, totalCredits: raw.totalsB?.credits ?? "0.0000" },
    areaBreakdownA: (raw.areaBreakdownA ?? []).map((item: any) => ({ code: item.area, name: item.name, share: item.share })),
    areaBreakdownB: (raw.areaBreakdownB ?? []).map((item: any) => ({ code: item.area, name: item.name, share: item.share })),
  };
}

function mapProfile(raw: any): UserProfile {
  const weights = (value: unknown) => Object.entries(record(value)).map(([code, weight]) => ({ code, name: code, weight: String(weight) }));
  return {
    interests: raw.interests ?? [],
    activityPreferences: raw.activityPreferences ?? [],
    antiInterests: (raw.antiInterests ?? []).map((item: any) => typeof item === "string" ? item : item.area),
    preferredSubjectWeights: weights(raw.preferredSubjectWeights),
    preferredActivityWeights: weights(raw.preferredActivityWeights),
    negativeWeights: weights(raw.negativeWeights),
    confidence: String(raw.confidence?.value ?? "0"),
    adaptiveAnswers: (raw.adaptiveAnswers ?? []).map((answer: any) => ({
      dimension: answer.dimension,
      value: answer.optionId,
    })),
  };
}

function mapProfileSnapshot(raw: any): UserProfileSnapshot {
  return {
    profile: mapProfile(raw.profile ?? raw),
    revision: String(raw.revision ?? "0"),
    createdAt: raw.createdAt ?? new Date().toISOString(),
    updatedAt: raw.updatedAt ?? new Date().toISOString(),
    expiresAt: raw.expiresAt ?? null,
  };
}

function mapRecommendation(raw: any): Recommendation {
  const mapShare = (value: unknown) => Object.entries(record(value)).map(([code, share]) => ({ code, name: code, share: String(share) }));
  const mapSemester = (value: unknown) => Object.entries(record(value)).map(([semester, share]) => ({ semester: Number(semester), share: String(share) }));
  const mapReason = (value: any) => ({
    area: value.area ?? null,
    activity: value.activity ?? null,
    text: value.text,
    workload: numberOrNull(value.workload),
    share: value.share ?? null,
    sourceNames: value.sourceNames ?? [],
  });
  const mapMetric = (value: any) => value ? { status: value.status ?? null, score: value.value ?? null } : null;
  return {
    programId: raw.programId,
    programCode: raw.programCode,
    programName: raw.programName,
    contentFit: raw.contentFit,
    score: {
      programId: raw.score?.programId ?? raw.programId,
      programCode: raw.score?.programCode ?? raw.programCode,
      programName: raw.programName,
      breakdown: raw.score?.breakdown ?? {
        subjectFit: "0",
        activityFit: "0",
        distinctiveFit: "0",
        antiPenalty: "0",
        rawContentFit: String(raw.contentFit ?? 0),
      },
    },
    reasons: (raw.reasons ?? []).map(mapReason),
    antiFitReasons: (raw.antiFitReasons ?? []).map(mapReason),
    areaShare: mapShare(raw.areaShare),
    semesterDistribution: mapSemester(raw.semesterDistribution),
    distinctiveSubjects: raw.distinctiveSubjects ?? [],
    workloadReadiness: mapMetric(raw.workloadReadiness),
    careerFit: mapMetric(raw.careerFit),
    admissionFit: mapMetric(raw.admissionFit),
  };
}

function mapRecommendations(raw: any): RecommendationsResponse {
  return {
    profile: mapProfile(raw.profile),
    recommendations: (raw.recommendations ?? []).map(mapRecommendation),
  };
}

function mapProftestSession(raw: ApiProftestSession): ProftestSessionResponse {
  const question = raw.currentQuestion;
  return {
    sessionId: raw.sessionId,
    questionSetVersion: raw.questionSetVersion,
    status: raw.status,
    cursor: raw.cursor,
    interactionCount: raw.interactionCount,
    revision: raw.revision,
    currentQuestion: question ? {
      id: question.id,
      block: question.block,
      prompt: question.prompt,
      options: question.options,
      required: question.required,
      adaptive: question.adaptive,
      multiSelect: question.multiSelect,
      maxSelected: question.maxSelected,
      stage: question.stage ?? null,
      componentType: question.componentType,
      order: question.order,
      helperText: question.helperText ?? null,
      declaredDimensions: question.declaredDimensions ?? [],
      allowUncertain: question.allowUncertain,
      allowSkip: question.allowSkip,
    } : null,
    staleQuestionIds: raw.staleQuestionIds ?? [],
    progress: raw.progress,
    adaptive: raw.adaptive ?? null,
    results: raw.results ? mapRecommendations(raw.results) : null,
  };
}

function mapEvent(raw: any): EventItem {
  return {
    id: raw.id,
    title: raw.title,
    kind: raw.kind,
    format: raw.format,
    startsAt: raw.startsAt,
    endsAt: raw.endsAt ?? null,
    description: raw.description ?? null,
    registrationUrl: raw.registrationUrl ?? null,
    universityIds: raw.universityIds ?? [],
    departmentIds: raw.departmentIds ?? [],
    programIds: raw.programIds ?? [],
    venue: raw.venue ? {
      id: raw.venue.id,
      name: raw.venue.name,
      address: raw.venue.address ?? null,
      latitude: numberOrNull(raw.venue.latitude),
      longitude: numberOrNull(raw.venue.longitude),
    } : null,
    provenance: (raw.provenance ?? []).map(mapProvenance),
  };
}

function mapPoint(raw: any): CampusPoint {
  return {
    id: raw.id,
    name: raw.name,
    pointType: raw.pointType,
    address: raw.address ?? null,
    latitude: numberOrNull(raw.latitude),
    longitude: numberOrNull(raw.longitude),
    universityIds: raw.universityIds ?? [],
    departmentIds: raw.departmentIds ?? [],
    programIds: raw.programIds ?? [],
    provenance: (raw.provenance ?? []).map(mapProvenance),
  };
}

function mapRoute(raw: any): PersonalRouteResponse {
  const recommendations = (raw.recommendations ?? []).map(mapRecommendation);
  const steps: PersonalRouteStep[] = (raw.steps ?? []).map((step: any) => {
    const point = step.point ? mapPoint(step.point) : null;
    return {
      position: step.position,
      kind: step.kind,
      reason: step.reason,
      programIds: step.programIds ?? [],
      recommendation: step.recommendation ? mapRecommendation(step.recommendation) : null,
      event: step.event ? mapEvent(step.event) : null,
      venue: point ? { id: point.id, name: point.name, address: point.address, latitude: point.latitude, longitude: point.longitude } : null,
      point,
      startsAt: step.startsAt ?? null,
    };
  });
  return { status: raw.status, summary: raw.summary, recommendations, steps };
}

function mapSession(raw: any): AuthSession {
  const account = record(raw.account) as AccountInfo & { accountId?: string };
  return {
    authenticated: Boolean(raw.authenticated),
    account: raw.account ? {
      id: account.accountId ?? account.id,
      email: account.email,
      displayName: account.displayName ?? null,
      createdAt: account.createdAt,
    } : null,
  };
}

function mapRun(raw: any): IngestionRunDetail {
  return {
    id: raw.id,
    source: raw.source ?? ((raw.sourceKinds ?? []).join(", ") || "bmstu_live"),
    status: raw.status,
    startedAt: raw.startedAt,
    finishedAt: raw.finishedAt ?? null,
    sourceCount: raw.sourceCount ?? 0,
    programCount: raw.programCount ?? 0,
    curriculumItemCount: raw.curriculumItemCount ?? 0,
    eventCount: raw.eventCount ?? 0,
    campusPointCount: raw.campusPointCount ?? 0,
    insertedCount: raw.insertedCount ?? 0,
    updatedCount: raw.updatedCount ?? 0,
    unchangedCount: raw.unchangedCount ?? 0,
    removedCount: raw.removedCount ?? 0,
    errorMessage: raw.errorMessage ?? null,
    sourceHashes: raw.sourceHashes ?? [],
    sourceKinds: raw.sourceKinds ?? [],
  };
}

function mapRunSummary(raw: any): IngestionRunSummary {
  const run = mapRun(raw);
  return run;
}

export function getPrograms(): Promise<ProgramListResponse> {
  return requestJson<ApiProgramList>("/programs").then((raw) => ({ items: raw.items.map(mapProgram) }));
}

export function getProgram(id: string): Promise<ProgramResponse> {
  return requestJson<ApiProgram>(`/programs/${encodeURIComponent(id)}`).then((raw) => ({ program: mapProgram(raw.program) }));
}

export function getCurriculumApi(id: string): Promise<CurriculumResponse> {
  return requestJson<ApiCurriculum>(`/programs/${encodeURIComponent(id)}/curriculum`).then(mapCurriculum);
}

export function getProgramAdmissions(id: string): Promise<ProgramAdmissionsResponse> {
  return requestJson<ApiAdmissions>(`/programs/${encodeURIComponent(id)}/admissions`).then(mapAdmissions);
}

export function calculateAdmissionFit(id: string, request: AdmissionFitRequest): Promise<AdmissionFitResponse> {
  return requestJson<ApiAdmissionFit>(`/programs/${encodeURIComponent(id)}/admission-fit`, {
    method: "POST",
    body: JSON.stringify(request),
  }).then(mapAdmissionFit);
}

export function comparePrograms(programIds: readonly [string, string], options: { scope?: "all" | "semester"; semester?: number } = {}): Promise<ComparisonResponse> {
  const params = new URLSearchParams({ programIds: programIds.join(","), scope: options.scope ?? "all" });
  if (options.semester !== undefined) params.set("semester", String(options.semester));
  return requestJson<ApiComparison>(`/compare?${params}`).then(mapComparison);
}

export function getDisciplineAreas(): Promise<{ items: DisciplineArea[] }> {
  return requestJson<{ items: any[] }>("/discipline-areas").then((raw) => ({
    items: raw.items.map((item) => ({ code: item.code, name: item.name, description: item.description, weight: "1" })),
  }));
}

export function getProftestQuestions(): Promise<QuestionnaireResponse> {
  return requestJson<ApiQuestions>("/proftest/questions");
}

export function previewProftestApi(request: ProftestSubmissionRequest): Promise<ProftestPreviewResponse> {
  return requestJson<ApiPreview>("/proftest/preview", { method: "POST", body: JSON.stringify(request) }).then((raw: any) => ({
    profile: mapProfile(raw.profile),
    adaptiveDecision: {
      dimension: raw.adaptive?.dimensions?.[0]?.code ?? "",
      decided: raw.adaptive?.status === "skipped",
      nextQuestion: raw.question ?? null,
    },
    candidates: (raw.candidates ?? []).map((candidate: any) => ({
      programId: candidate.programId,
      programName: candidate.programCode,
      contentFit: candidate.contentFit,
    })),
  }));
}

export function getProftestResultsApi(request: ProftestSubmissionRequest): Promise<ProftestResultsResponse> {
  return requestJson<ApiResults>("/proftest/results", { method: "POST", body: JSON.stringify(request) }).then(mapRecommendations);
}

export function startProftestSession(): Promise<ProftestSessionResponse> {
  return requestJson<ApiProftestSession>("/proftest/sessions", { method: "POST", body: "{}" }).then(mapProftestSession);
}

export function getCurrentProftestSession(): Promise<ProftestSessionResponse> {
  return requestJson<ApiProftestSession>("/proftest/sessions/current").then(mapProftestSession);
}

export function nextProftestSession(answer: ProftestSessionAnswerRequest, expectedRevision: number): Promise<ProftestSessionResponse> {
  const request: ApiProftestSessionNext = { ...answer, expectedRevision };
  return requestJson<ApiProftestSession>("/proftest/sessions/current/next", { method: "POST", body: JSON.stringify(request) }).then(mapProftestSession);
}

export function saveProftestSession(answers: readonly ProftestSessionAnswerRequest[], expectedRevision: number): Promise<ProftestSessionResponse> {
  const request: ApiProftestSessionPatch = { answers: [...answers], expectedRevision };
  return requestJson<ApiProftestSession>("/proftest/sessions/current", { method: "PATCH", body: JSON.stringify(request) }).then(mapProftestSession);
}

export function completeProftestSession(): Promise<ProftestSessionResponse> {
  return requestJson<ApiProftestSession>("/proftest/sessions/current/complete", { method: "POST", body: "{}" }).then(mapProftestSession);
}

export function sendProftestAnalytics(request: ApiProftestAnalytics): Promise<{ accepted: number }> {
  return requestJson<{ accepted: number }>("/proftest/analytics", { method: "POST", body: JSON.stringify(request) });
}

export function getCurrentProfile(): Promise<UserProfileSnapshot> {
  return requestJson<ApiProfile>("/proftest/profile").then(mapProfileSnapshot);
}

export function getCurrentRecommendations(limit = 10): Promise<RecommendationsResponse> {
  return requestJson<ApiRecommendations>(`/recommendations/current?limit=${encodeURIComponent(String(limit))}`).then(mapRecommendations);
}

export type EventQuery = {
  from?: string;
  to?: string;
  kind?: string;
  format?: string;
  universityId?: string;
  departmentId?: string;
  programId?: string;
  recommended?: boolean;
  limit?: number;
};

function queryString(options: Record<string, string | number | boolean | undefined>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(options)) if (value !== undefined) params.set(key, String(value));
  const encoded = params.toString();
  return encoded ? `?${encoded}` : "";
}

export function getEvents(options: EventQuery = {}): Promise<EventListResponse> {
  return requestJson<ApiEvents>(`/events${queryString(options)}`).then((raw) => ({ items: raw.items.map(mapEvent), total: raw.total }));
}

export function getEventApi(id: string): Promise<EventDetailResponse> {
  return requestJson<ApiEvent>(`/events/${encodeURIComponent(id)}`).then((raw) => ({ event: mapEvent(raw.event) }));
}

export function getCampusPointApi(id: string): Promise<CampusPointDetailResponse> {
  return requestJson<ApiPoint>(`/campus/points/${encodeURIComponent(id)}`).then((raw) => ({ point: mapPoint(raw) }));
}

export function getCampusPointEventsApi(id: string): Promise<CampusPointEventsResponse> {
  return requestJson<ApiPointEvents>(`/campus/points/${encodeURIComponent(id)}/events`).then((raw) => ({
    pointId: raw.pointId,
    items: raw.items.map(mapEvent),
    total: raw.total,
  }));
}

export function getCampusRecommendations(): Promise<CampusRecommendationsResponse> {
  return requestJson<ApiCampusRecommendations>("/campus/recommendations").then((raw) => ({
    recommendedProgramIds: raw.recommendedProgramIds,
    recommendations: raw.recommendations.map(mapRecommendation),
    points: raw.points.map(mapPoint),
    events: raw.events.map(mapEvent),
    eventsWithoutPoint: raw.eventsWithoutPoint.map(mapEvent),
  }));
}

export function getPersonalRouteApi(): Promise<PersonalRouteResponse> {
  return requestJson<ApiRoute>("/personal-route").then(mapRoute);
}

export function getAuthSessionApi(): Promise<AuthSession> {
  return requestJson<ApiSession>("/auth/session").then(mapSession);
}

export function registerAccountApi(email: string, password: string): Promise<AuthSession> {
  return requestJson<ApiSession>("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }).then(mapSession);
}

export function loginAccountApi(email: string, password: string): Promise<AuthSession> {
  return requestJson<ApiSession>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }).then(mapSession);
}

export function logoutAccountApi(): Promise<AuthSession> {
  return requestJson<ApiSession>("/auth/logout", { method: "POST" }).then(mapSession);
}

function opsHeaders(opsKey: string): HeadersInit {
  return { "X-Andromeda-Ops-Key": opsKey };
}

export function getIngestionRunsApi(options: { status?: IngestionRunStatus; limit?: number } = {}, opsKey: string): Promise<IngestionRunListResponse> {
  return requestJson<ApiRuns>(`/ops/ingestion/runs${queryString(options)}`, { headers: opsHeaders(opsKey) }).then((raw) => ({
    items: raw.items.map(mapRunSummary),
    total: raw.total,
  }));
}

export function getIngestionRunApi(id: string, opsKey: string): Promise<IngestionRunDetailResponse> {
  return requestJson<ApiRun>(`/ops/ingestion/runs/${encodeURIComponent(id)}`, { headers: opsHeaders(opsKey) }).then((raw) => ({ run: mapRun(raw.run) }));
}

export function retryIngestionApi(request: IngestionRetryRequest, opsKey: string): Promise<IngestionRunDetailResponse> {
  return requestJson<ApiRetry>("/ops/ingestion/runs/retry", {
    method: "POST",
    headers: opsHeaders(opsKey),
    body: JSON.stringify(request),
  }).then((raw) => ({ run: mapRun(raw.run) }));
}
