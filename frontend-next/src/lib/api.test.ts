import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, ApiTimeoutError, API_REQUEST_TIMEOUT_MS, getCurrentProftestSession, getCurrentRecommendations, getPrograms } from "./api";

describe("canonical API client", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("maps the catalog response without a fixture fallback", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      items: [{ id: "program:01", directionId: "01.03.02", code: "01.03.02-01", name: "Программа", educationYear: 2026, studyPlanUrl: null, sourceUrl: null }],
    }), { status: 200, headers: { "Content-Type": "application/json" } })));

    await expect(getPrograms()).resolves.toEqual({
      items: [{ id: "program:01", directionId: "01.03.02", code: "01.03.02-01", name: "Программа", educationYear: "2026", studyPlanUrl: null, sourceUrl: null }],
    });
    expect(fetch).toHaveBeenCalledWith("/api/programs", expect.objectContaining({ credentials: "include", cache: "no-store" }));
  });

  it("exposes structured API errors to feature boundaries", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      code: "NOT_FOUND",
      message: "Профиль не найден",
      details: [],
    }), { status: 404, headers: { "Content-Type": "application/json" } })));

    await expect(getCurrentRecommendations()).rejects.toEqual(expect.objectContaining({
      constructor: ApiError,
      status: 404,
      payload: expect.objectContaining({ code: "NOT_FOUND" }),
    }));
  });

  it("turns an aborted fetch into a typed timeout", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn((_input: RequestInfo | URL, init?: RequestInit) => new Promise((_resolve, reject) => {
      init?.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
    })));

    const pending = getCurrentRecommendations();
    const assertion = expect(pending).rejects.toMatchObject({
      constructor: ApiTimeoutError,
      path: "/recommendations/current?limit=10",
      timeoutMs: API_REQUEST_TIMEOUT_MS,
    });
    await vi.advanceTimersByTimeAsync(API_REQUEST_TIMEOUT_MS);
    await assertion;
  });

  it("maps a stopped preliminary proftest response without numeric leakage", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      sessionId: "proftest-session:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      questionSetVersion: "proftest-v3",
      status: "draft",
      cursor: 5,
      interactionCount: 5,
      revision: 6,
      currentQuestion: null,
      staleQuestionIds: [],
      progress: { stage: "clarification", stageIndex: 5, stageCount: 6, answerCount: 5, minRemaining: 0, maxRemaining: 4 },
      adaptive: { status: "skipped", reason: "stable", candidateCount: 4, topCandidateCount: 4, dimensions: [], askedQuestionIds: [], uncertainDimensions: [], adaptiveCount: 0, stopReason: "no_meaningful_question" },
      preliminary: { topics: [{ code: "area:computer_science_data", label: "Информатика и данные" }] },
      results: null,
    }), { status: 200, headers: { "Content-Type": "application/json" } })));

    await expect(getCurrentProftestSession()).resolves.toEqual(expect.objectContaining({
      questionSetVersion: "proftest-v3",
      currentQuestion: null,
      preliminary: { topics: [{ code: "area:computer_science_data", label: "Информатика и данные" }] },
      adaptive: expect.objectContaining({ stopReason: "no_meaningful_question" }),
    }));
  });
});
