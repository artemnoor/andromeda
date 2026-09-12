import { describe, expect, it } from "vitest";

import type { EventListResponse } from "../../api/client";

import { renderEventsList } from "./EventsList";

function fakeRoot(): HTMLElement {
  return { innerHTML: "" } as HTMLElement;
}

const response: EventListResponse = {
  total: 1,
  items: [{
    id: "event:bmstu:online",
    title: "Онлайн",
    kind: "lecture",
    format: "online",
    startsAt: "2026-12-01T10:00:00Z",
    endsAt: null,
    description: null,
    registrationUrl: null,
    universityIds: ["university:bmstu"],
    departmentIds: [],
    programIds: [],
    venue: null,
    provenance: [{ kind: "bmstu_events", url: "https://bmstu.ru/events", capturedAt: "2026-09-12T08:00:00Z", contentSha256: "a".repeat(64) }],
  }],
};

describe("event list", () => {
  it("renders empty and populated states", () => {
    const root = fakeRoot();
    renderEventsList(root, { total: 0, items: [] }, [], false);
    expect(root.innerHTML).toContain("Событий не найдено");
    renderEventsList(root, response, [], false);
    expect(root.innerHTML).toContain("Онлайн");
    expect(root.innerHTML).toContain("data-testid=\"events-count\">1 событий");
  });
});
