import { describe, expect, it } from "vitest";

import { toQuery } from "./EventsPage";

describe("event page query", () => {
  it("serializes kind, format, date window, and recommendation mode", () => {
    const query = toQuery({ kind: "additional_education", format: "hybrid", from: "2026-10-01", to: "2026-10-31", recommended: true });
    expect(query.kind).toBe("additional_education");
    expect(query.format).toBe("hybrid");
    expect(query.from).toBe(new Date("2026-10-01T00:00:00").toISOString());
    expect(query.to).toBe(new Date("2026-10-31T23:59:59").toISOString());
    expect(query.recommended).toBe(true);
  });
});
