import { afterEach, describe, expect, it } from "vitest";

import { loadPersistedResults } from "./profilePersistence";

const originalFetch = globalThis.fetch;

const profile = {
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
});

describe("server-backed proftest restore", () => {
  it("combines the persisted profile with current recommendations", async () => {
    globalThis.fetch = async (input) => {
      const path = String(input);
      if (path === "/proftest/profile") return new Response(JSON.stringify({ profile, profileId: "profile:a", revision: 2, createdAt: "2027-01-01T00:00:00Z", updatedAt: "2027-01-01T00:00:00Z", expiresAt: "2027-02-01T00:00:00Z" }), { status: 200 });
      return new Response(JSON.stringify({ profile, recommendations: [] }), { status: 200 });
    };

    const results = await loadPersistedResults();

    expect(results?.profile).toEqual(profile);
    expect(results?.recommendations).toEqual([]);
  });

  it("treats a missing current profile as the normal empty path", async () => {
    globalThis.fetch = async () => new Response(JSON.stringify({ code: "NOT_FOUND", message: "Current profile was not found", details: [] }), { status: 404 });

    await expect(loadPersistedResults()).resolves.toBeNull();
  });
});
