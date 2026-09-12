import type { components, paths } from "./generated";
import { ApiError, isErrorResponse } from "./errors";

type ProgramResponse = paths["/programs/{id}"]["get"]["responses"][200]["content"]["application/json"];
type ProgramListResponse = paths["/programs"]["get"]["responses"][200]["content"]["application/json"];
type CurriculumResponse = paths["/programs/{id}/curriculum"]["get"]["responses"][200]["content"]["application/json"];
type ProgramAdmissionsResponse = paths["/programs/{id}/admissions"]["get"]["responses"][200]["content"]["application/json"];
type AdmissionFitRequest = NonNullable<paths["/programs/{id}/admission-fit"]["post"]["requestBody"]>["content"]["application/json"];
type AdmissionFitResponse = paths["/programs/{id}/admission-fit"]["post"]["responses"][200]["content"]["application/json"];
type CompareResponse = paths["/compare"]["get"]["responses"][200]["content"]["application/json"];
type QuestionnaireResponse = paths["/proftest/questions"]["get"]["responses"][200]["content"]["application/json"];
type ProftestRequest = NonNullable<paths["/proftest/preview"]["post"]["requestBody"]>["content"]["application/json"];
type ProftestPreviewResponse = paths["/proftest/preview"]["post"]["responses"][200]["content"]["application/json"];
type ProftestResultsResponse = paths["/proftest/results"]["post"]["responses"][200]["content"]["application/json"];
type CurrentProfileResponse = paths["/proftest/profile"]["get"]["responses"][200]["content"]["application/json"];
type CreateProfileRequest = NonNullable<paths["/proftest/profile"]["post"]["requestBody"]>["content"]["application/json"];
type UpdateProfileRequest = NonNullable<paths["/proftest/profile"]["put"]["requestBody"]>["content"]["application/json"];
type RecommendationRequest = NonNullable<paths["/recommendations"]["post"]["requestBody"]>["content"]["application/json"];
type RecommendationsResponse = paths["/recommendations"]["post"]["responses"][200]["content"]["application/json"];
type CurrentRecommendationsResponse = paths["/recommendations/current"]["get"]["responses"][200]["content"]["application/json"];
type ErrorContract = components["schemas"]["ErrorResponse"];

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";
const logLevel = (import.meta.env.VITE_LOG_LEVEL as string | undefined) ?? "WARN";

function debug(message: string): void {
  if (logLevel === "DEBUG") console.debug(`[api] ${message}`);
}

async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  debug(`request_start path=${path}`);
  const response = await fetch(`${apiBaseUrl}${path}`, { ...init, credentials: "include", headers: { Accept: "application/json", "Content-Type": "application/json", ...init.headers } });
  const payload: unknown = await response.json();
  if (!response.ok) {
    console.warn(`[api] request_failed status=${response.status}`);
    if (isErrorResponse(payload)) throw new ApiError(response.status, payload);
    throw new Error(`API request failed with ${response.status}`);
  }
  debug(`request_complete path=${path} status=${response.status}`);
  return payload as T;
}

export function getProgram(id: string): Promise<ProgramResponse> {
  return requestJson<ProgramResponse>(`/programs/${encodeURIComponent(id)}`);
}

export function getPrograms(): Promise<ProgramListResponse> {
  return requestJson<ProgramListResponse>("/programs");
}

export function getCurriculum(id: string): Promise<CurriculumResponse> {
  return requestJson<CurriculumResponse>(`/programs/${encodeURIComponent(id)}/curriculum`);
}

export function getProgramAdmissions(id: string): Promise<ProgramAdmissionsResponse> {
  return requestJson<ProgramAdmissionsResponse>(`/programs/${encodeURIComponent(id)}/admissions`);
}

export function calculateAdmissionFit(id: string, request: AdmissionFitRequest): Promise<AdmissionFitResponse> {
  return requestJson<AdmissionFitResponse>("/programs/" + encodeURIComponent(id) + "/admission-fit", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export function comparePrograms(
  programIds: readonly [string, string],
  options: { scope?: components["schemas"]["ComparisonScope"]; semester?: number | undefined } = {},
): Promise<CompareResponse> {
  const params = new URLSearchParams({ programIds: programIds.join(","), scope: options.scope ?? "all" });
  if (options.semester !== undefined) params.set("semester", String(options.semester));
  return requestJson<CompareResponse>(`/compare?${params.toString()}`);
}

export function getProftestQuestions(): Promise<QuestionnaireResponse> {
  return requestJson<QuestionnaireResponse>("/proftest/questions");
}

export function previewProftest(request: ProftestRequest): Promise<ProftestPreviewResponse> {
  return requestJson<ProftestPreviewResponse>("/proftest/preview", { method: "POST", body: JSON.stringify(request) });
}

export function getProftestResults(request: ProftestRequest): Promise<ProftestResultsResponse> {
  return requestJson<ProftestResultsResponse>("/proftest/results", { method: "POST", body: JSON.stringify(request) });
}

export function getCurrentProfile(): Promise<CurrentProfileResponse> {
  return requestJson<CurrentProfileResponse>("/proftest/profile");
}

export function createCurrentProfile(request: CreateProfileRequest): Promise<CurrentProfileResponse> {
  return requestJson<CurrentProfileResponse>("/proftest/profile", { method: "POST", body: JSON.stringify(request) });
}

export function updateCurrentProfile(request: UpdateProfileRequest): Promise<CurrentProfileResponse> {
  return requestJson<CurrentProfileResponse>("/proftest/profile", { method: "PUT", body: JSON.stringify(request) });
}

export function getRecommendations(request: RecommendationRequest): Promise<RecommendationsResponse> {
  return requestJson<RecommendationsResponse>("/recommendations", { method: "POST", body: JSON.stringify(request) });
}

export function getCurrentRecommendations(limit = 10): Promise<CurrentRecommendationsResponse> {
  return requestJson<CurrentRecommendationsResponse>(`/recommendations/current?limit=${encodeURIComponent(String(limit))}`);
}

export type { AdmissionFitRequest, AdmissionFitResponse, CompareResponse, CreateProfileRequest, CurrentProfileResponse, CurrentRecommendationsResponse, CurriculumResponse, ErrorContract, ProftestPreviewResponse, ProftestRequest, ProftestResultsResponse, ProgramAdmissionsResponse, ProgramListResponse, ProgramResponse, QuestionnaireResponse, RecommendationRequest, RecommendationsResponse, UpdateProfileRequest };
