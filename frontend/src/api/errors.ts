export type ErrorDetail = {
  path: string;
  message: string;
  type: string;
};

export type ErrorResponse = {
  code: string;
  message: string;
  details: ErrorDetail[];
};

export function isErrorResponse(value: unknown): value is ErrorResponse {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.code === "string" &&
    typeof record.message === "string" &&
    Array.isArray(record.details) &&
    record.details.every((detail: unknown) => {
      if (typeof detail !== "object" || detail === null) return false;
      const item = detail as Record<string, unknown>;
      return typeof item.path === "string" && typeof item.message === "string" && typeof item.type === "string";
    })
  );
}

export class ApiError extends Error {
  readonly status: number;
  readonly payload: ErrorResponse;

  constructor(status: number, payload: ErrorResponse) {
    super(payload.message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export class ApiTimeoutError extends Error {
  readonly path: string;
  readonly timeoutMs: number;

  constructor(path: string, timeoutMs: number) {
    super(`API request timed out after ${timeoutMs}ms`);
    this.name = "ApiTimeoutError";
    this.path = path;
    this.timeoutMs = timeoutMs;
  }
}
