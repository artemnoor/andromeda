import type { ErrorResponse } from "./generated";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, payload: ErrorResponse | null) {
    super(payload?.message ?? `API request failed (${status})`);
    this.name = "ApiError";
    this.status = status;
    this.code = payload?.code ?? "request_failed";
  }
}

export function isErrorResponse(value: unknown): value is ErrorResponse {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Record<string, unknown>;
  return typeof candidate.code === "string" && typeof candidate.message === "string";
}
