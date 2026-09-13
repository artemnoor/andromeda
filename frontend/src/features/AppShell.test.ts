import { describe, expect, it } from "vitest";

import { hashForFeature, parseFeatureHash } from "./AppShell";

describe("AppShell hash navigation", () => {
  it("opens the unified flow and preserves existing feature hashes", () => {
    expect(parseFeatureHash("#flow")).toEqual({ feature: "flow" });
    expect(parseFeatureHash("#compare")).toEqual({ feature: "compare" });
    expect(parseFeatureHash("#events")).toEqual({ feature: "events" });
    expect(parseFeatureHash("#personal-route")).toEqual({ feature: "personal-route" });
    expect(parseFeatureHash("#proftest")).toEqual({ feature: "proftest" });
  });

  it("keeps program IDs encoded in the existing program entrypoint", () => {
    expect(parseFeatureHash("#program/program%3A09.03.01-02")).toEqual({ feature: "program", programId: "program:09.03.01-02" });
    expect(hashForFeature("program", "program:09.03.01-02")).toBe("#program/program%3A09.03.01-02");
    expect(hashForFeature("flow")).toBe("#flow");
  });

  it("keeps compare as the safe fallback for unknown hashes", () => {
    expect(parseFeatureHash("")).toEqual({ feature: "compare" });
    expect(parseFeatureHash("#unknown")).toEqual({ feature: "compare" });
  });
});
