import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  ApiTimeoutError,
  API_REQUEST_TIMEOUT_MS,
  addDecisionShortlist,
  getCurrentProftestSession,
  getCurrentRecommendations,
  getDecisionContext,
  getComparisonSummary,
  getPrograms,
} from "./api";

const decisionContextPayload = {
  decisionId: "decision:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  state: {
    version: 1,
    admissionConstraints: null,
    choice: {
      consideredProgramIds: ["program:01"],
      shortlistEntries: [{
        programId: "program:01",
        role: "primary",
        state: "active",
        origin: "user",
        revision: 2,
        createdAt: "2026-09-17T10:00:00Z",
        updatedAt: "2026-09-17T10:00:00Z",
        removedAt: null,
      }],
      excludedProgramIds: [],
    },
    explicitPriorities: [],
    revision: 2,
    createdAt: "2026-09-17T10:00:00Z",
    updatedAt: "2026-09-17T10:00:00Z",
  },
  preferences: null,
  profileRevision: null,
  missingData: ["admission_constraints"],
  metadata: {
    decisionId: "decision:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    revision: 2,
    status: "active",
    createdAt: "2026-09-17T10:00:00Z",
    updatedAt: "2026-09-17T10:00:00Z",
    profileRevision: null,
  },
};

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
      items: [{ id: "program:01", directionId: "01.03.02", code: "01.03.02-01", name: "Программа", educationYear: "2026", studyPlanUrl: null, sourceUrl: null, universityId: null, universityName: null }],
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

  it("uses the generated decision route and preserves the explicit context shape", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(decisionContextPayload), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })));

    await expect(getDecisionContext()).resolves.toMatchObject({
      decisionId: decisionContextPayload.decisionId,
      state: { revision: 2, choice: { shortlistEntries: [{ programId: "program:01", state: "active" }] } },
      missingData: ["admission_constraints"],
    });
    expect(fetch).toHaveBeenCalledWith("/api/decision/context", expect.objectContaining({
      credentials: "include",
      cache: "no-store",
    }));
  });

  it("sends an explicit shortlist command with the server revision", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      decisionId: decisionContextPayload.decisionId,
      context: decisionContextPayload,
      changed: true,
    }), { status: 200, headers: { "Content-Type": "application/json" } })));

    await addDecisionShortlist("program:01", "alternative", 2);

    const [, init] = vi.mocked(fetch).mock.calls[0] as [RequestInfo | URL, RequestInit];
    expect(fetch).toHaveBeenCalledWith("/api/decision/shortlist", expect.objectContaining({ method: "POST" }));
    expect(JSON.parse(String(init.body))).toEqual({
      version: 1,
      programId: "program:01",
      role: "alternative",
      expectedRevision: 2,
    });
  });

  it("keeps comparison summary selection separate from shortlist mutations", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      programs: [],
      scope: "all",
      semester: null,
      keyDifferences: [],
      tradeoffs: [],
      sourceGaps: [],
    }), { status: 200, headers: { "Content-Type": "application/json" } })));

    await expect(getComparisonSummary(["program:01.03.02-01", "program:01.03.02-02", "program:01.03.02-03"])).resolves.toEqual(expect.objectContaining({ programs: [] }));
    expect(fetch).toHaveBeenCalledWith(
      "/api/compare/summary?programIds=program%3A01.03.02-01%2Cprogram%3A01.03.02-02%2Cprogram%3A01.03.02-03&scope=all",
      expect.objectContaining({ credentials: "include", cache: "no-store" }),
    );
  });
});
