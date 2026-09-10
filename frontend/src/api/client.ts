import type { components, paths } from "./generated";
import { ApiError, isErrorResponse } from "./errors";

type ProgramResponse = paths["/programs/{id}"]["get"]["responses"][200]["content"]["application/json"];
type CurriculumResponse = paths["/programs/{id}/curriculum"]["get"]["responses"][200]["content"]["application/json"];
type CompareResponse = paths["/compare"]["get"]["responses"][200]["content"]["application/json"];
type ErrorContract = components["schemas"]["ErrorResponse"];

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";
const logLevel = (import.meta.env.VITE_LOG_LEVEL as string | undefined) ?? "WARN";

function debug(message: string): void {
  if (logLevel === "DEBUG") console.debug(`[api] ${message}`);
}

async function requestJson<T>(path: string): Promise<T> {
  debug(`request_start path=${path}`);
  const response = await fetch(`${apiBaseUrl}${path}`, { headers: { Accept: "application/json" } });
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

export function getCurriculum(id: string): Promise<CurriculumResponse> {
  return requestJson<CurriculumResponse>(`/programs/${encodeURIComponent(id)}/curriculum`);
}

export function comparePrograms(programIds: readonly [string, string]): Promise<CompareResponse> {
  const query = encodeURIComponent(programIds.join(","));
  return requestJson<CompareResponse>(`/compare?programIds=${query}`);
}

export type { CompareResponse, CurriculumResponse, ErrorContract, ProgramResponse };
