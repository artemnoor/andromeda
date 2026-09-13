import type {
  BootstrapResponse,
  ErrorResponse,
  PreviewResponse,
  ResultsResponse,
  TestAnswersRequest
} from "./generated";
import { ApiError, isErrorResponse } from "./errors";

export { ApiError } from "./errors";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";
const logLevel = ((import.meta.env.VITE_LOG_LEVEL as string | undefined) ?? "WARN").toUpperCase();

function debug(message: string): void {
  if (logLevel === "DEBUG") console.debug(`[proftest-spike] ${message}`);
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  debug(`request_start method=${init?.method ?? "GET"} path=${path}`);
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      headers: { Accept: "application/json", "Content-Type": "application/json", ...init?.headers }
    });
  } catch {
    console.warn(`[proftest-spike] request_unavailable path=${path}`);
    throw new ApiError(503, { code: "upstream_unavailable", message: "Сервис временно недоступен" } satisfies ErrorResponse);
  }
  const raw: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    console.warn(`[proftest-spike] request_failed status=${response.status}`);
    throw new ApiError(response.status, isErrorResponse(raw) ? raw : null);
  }
  debug(`request_complete method=${init?.method ?? "GET"} path=${path} status=${response.status}`);
  return raw as T;
}

export function getBootstrap(): Promise<BootstrapResponse> {
  return requestJson<BootstrapResponse>("/api/test/bootstrap");
}

export function previewTest(payload: TestAnswersRequest): Promise<PreviewResponse> {
  return requestJson<PreviewResponse>("/api/test/preview", { method: "POST", body: JSON.stringify(payload) });
}

export function getResults(payload: TestAnswersRequest): Promise<ResultsResponse> {
  return requestJson<ResultsResponse>("/api/test/results", { method: "POST", body: JSON.stringify(payload) });
}
