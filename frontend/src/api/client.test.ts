import { afterEach, describe, expect, it, vi } from "vitest";

import { createCurrentProfile, getCurrentProfile, getCurrentRecommendations, getEvents, getPersonalRoute, updateCurrentProfile, type CreateProfileRequest, type UpdateProfileRequest } from "./client";

const originalFetch = globalThis.fetch;
const profile: CreateProfileRequest["profile"] = {
  version: 1,
  interests: [],
  activityPreferences: [],
  antiInterests: [],
  preferredSubjectWeights: {},
  preferredActivityWeights: {},
  negativeWeights: {},
  confidence: { value: "0", answeredBase: 0, answeredAdaptive: 0 },
  adaptiveAnswers: [],
};

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
});

describe("typed API client", () => {
  it("sends anonymous credentials for current profile requests", async () => {
    const fetchMock = vi.fn<typeof fetch>(async () => new Response(JSON.stringify({}), { status: 200 }));
    globalThis.fetch = fetchMock;

    await getCurrentProfile();

    expect(fetchMock).toHaveBeenCalledWith(
      "/proftest/profile",
      expect.objectContaining({ credentials: "include", headers: expect.objectContaining({ Accept: "application/json" }) }),
    );
  });

  it("keeps current recommendation query typed and does not log response bodies", async () => {
    const fetchMock = vi.fn<typeof fetch>(async () => new Response(JSON.stringify({ recommendations: [], profile: {} }), { status: 200 }));
    const debug = vi.spyOn(console, "debug").mockImplementation(() => undefined);
    globalThis.fetch = fetchMock;

    await getCurrentRecommendations(3);

    expect(fetchMock.mock.calls[0]?.[0]).toBe("/recommendations/current?limit=3");
    expect(fetchMock.mock.calls[0]?.[1]).toEqual(expect.objectContaining({ credentials: "include" }));
    expect(debug).not.toHaveBeenCalledWith(expect.stringContaining("profile"));
  });

  it("sends create and optimistic-update payloads without losing the revision", async () => {
    const fetchMock = vi.fn<typeof fetch>(async () => new Response(JSON.stringify({}), { status: 200 }));
    globalThis.fetch = fetchMock;
    const createRequest: CreateProfileRequest = { profile };
    const updateRequest: UpdateProfileRequest = { profile, expectedRevision: 4 };

    await createCurrentProfile(createRequest);
    await updateCurrentProfile(updateRequest);

    expect(fetchMock.mock.calls[0]?.[0]).toBe("/proftest/profile");
    expect(fetchMock.mock.calls[0]?.[1]).toEqual(expect.objectContaining({ method: "POST", body: JSON.stringify(createRequest), credentials: "include" }));
    expect(fetchMock.mock.calls[1]?.[1]).toEqual(expect.objectContaining({ method: "PUT", body: JSON.stringify(updateRequest), credentials: "include" }));
  });

  it("serializes event filters through the generated query contract", async () => {
    const fetchMock = vi.fn<typeof fetch>(async () => new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }));
    globalThis.fetch = fetchMock;

    await getEvents({ kind: "additional_education", format: "offline", programId: "program:09.03.01-02", recommended: true, limit: 10 });

    expect(fetchMock.mock.calls[0]?.[0]).toBe("/events?kind=additional_education&format=offline&programId=program%3A09.03.01-02&recommended=true&limit=10");
    expect(fetchMock.mock.calls[0]?.[1]).toEqual(expect.objectContaining({ credentials: "include" }));
  });

  it("requests the logical personal plan with the bounded limit", async () => {
    const fetchMock = vi.fn<typeof fetch>(async () => new Response(JSON.stringify({ status: "no_recommendations", summary: "empty", recommendations: [], steps: [] }), { status: 200 }));
    globalThis.fetch = fetchMock;

    await getPersonalRoute(4);

    expect(fetchMock.mock.calls[0]?.[0]).toBe("/personal-route?limit=4");
    expect(fetchMock.mock.calls[0]?.[1]).toEqual(expect.objectContaining({ credentials: "include" }));
  });
});
