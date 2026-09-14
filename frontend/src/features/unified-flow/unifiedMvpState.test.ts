import { beforeEach, describe, expect, it, vi } from "vitest";

import { getCurrentProfile, getCurrentRecommendations, getEvents } from "../../api/client";
import { ApiError } from "../../api/errors";
import { deriveUnifiedMvpStages, loadUnifiedMvpState, type UnifiedReadModel } from "./unifiedMvpState";

vi.mock("../../api/client", () => ({
  getCurrentProfile: vi.fn(),
  getCurrentRecommendations: vi.fn(),
  getEvents: vi.fn(),
}));

const profile = vi.mocked(getCurrentProfile);
const recommendations = vi.mocked(getCurrentRecommendations);
const events = vi.mocked(getEvents);

function apiError(status: number): ApiError {
  return new ApiError(status, { code: "TEST", message: "test error", details: [] });
}

describe("unified MVP state", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("reads profile and recommendations independently and then reads recommended events", async () => {
    profile.mockResolvedValue({ profile: {} } as never);
    recommendations.mockResolvedValue({ recommendations: [{ programId: "program:09.03.01-02" }] } as never);
    events.mockResolvedValue({ items: [{ id: "event:bmstu:open-day" }] } as never);

    await expect(loadUnifiedMvpState()).resolves.toEqual({
      profile: { status: "ready" },
      recommendations: { status: "ready", count: 1, firstProgramId: "program:09.03.01-02" },
      events: { status: "ready", count: 1 },
    });
    expect(getEvents).toHaveBeenCalledWith({ recommended: true, limit: 4 });
  });

  it("classifies a missing profile and skips recommended events", async () => {
    profile.mockRejectedValue(apiError(404));
    recommendations.mockRejectedValue(apiError(404));

    await expect(loadUnifiedMvpState()).resolves.toMatchObject({
      profile: { status: "profile-required" },
      recommendations: { status: "profile-required", count: 0 },
      events: { status: "profile-required", count: 0 },
    });
    expect(getEvents).not.toHaveBeenCalled();
  });

  it("keeps a ready profile and events when recommendations are empty", async () => {
    profile.mockResolvedValue({ profile: {} } as never);
    recommendations.mockResolvedValue({ recommendations: [] } as never);
    events.mockResolvedValue({ items: [] } as never);

    await expect(loadUnifiedMvpState()).resolves.toMatchObject({
      profile: { status: "ready" },
      recommendations: { status: "empty", count: 0 },
      events: { status: "empty", count: 0 },
    });
  });

  it("keeps other stages available when one read branch fails", () => {
    const model: UnifiedReadModel = {
      profile: { status: "ready" },
      recommendations: { status: "error", count: 0 },
      events: { status: "ready", count: 2 },
    };

    const stages = deriveUnifiedMvpStages(model);
    expect(stages.map((stage) => stage.id)).toEqual(["catalog", "compare", "profile", "recommendations", "program", "admission-fit", "events", "personal-route"]);
    expect(stages.find((stage) => stage.id === "compare")?.href).toBe("#compare");
    expect(stages.find((stage) => stage.id === "events")?.href).toBe("#events");
    expect(stages.find((stage) => stage.id === "recommendations")?.status).toBe("error");
  });

  it("encodes the canonical recommended program ID in program links", () => {
    const model: UnifiedReadModel = {
      profile: { status: "ready" },
      recommendations: { status: "ready", count: 1, firstProgramId: "program:09.03.01/02" },
      events: { status: "empty", count: 0 },
    };

    const stages = deriveUnifiedMvpStages(model);
    expect(stages.find((stage) => stage.id === "program")?.href).toBe("#program/program%3A09.03.01%2F02");
    expect(stages.find((stage) => stage.id === "admission-fit")?.href).toBe("#program/program%3A09.03.01%2F02");
  });
});
