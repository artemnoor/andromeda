import { describe, expect, it } from "vitest";

import type { EventResponse } from "../../api/client";

import { renderEventCard } from "./EventsCard";

const event: EventResponse["event"] = {
  id: "event:bmstu:sample",
  title: "<script>alert(1)</script>",
  kind: "additional_education",
  format: "offline",
  startsAt: "2026-10-17T11:00:00+03:00",
  endsAt: "2026-10-17T15:00:00+03:00",
  description: "Описание <strong>события</strong>",
  registrationUrl: "https://bmstu.ru/events/register",
  universityIds: ["university:bmstu"],
  departmentIds: ["department:bmstu:iu7"],
  programIds: ["program:09.03.01-02"],
  venue: {
    id: "venue:bmstu:main-campus",
    name: "Главный корпус",
    address: "Москва, 2-я Бауманская, 5",
    latitude: "55.766600",
    longitude: "37.685500",
  },
  provenance: [{ kind: "bmstu_events", url: "https://bmstu.ru/events", capturedAt: "2026-09-12T08:00:00Z", contentSha256: "a".repeat(64), locator: "events" }],
};

describe("event cards", () => {
  it("renders source fields, coordinates, registration, and escaped text", () => {
    const html = renderEventCard(event, [{ id: "program:09.03.01-02", directionId: "direction:09.03.01", code: "09.03.01-02", name: "Информатика", educationYear: 2026, studyPlanUrl: "https://bmstu.ru/plan.pdf", sourceUrl: "https://bmstu.ru/program" }]);
    expect(html).toContain("ДОД");
    expect(html).toContain("Координаты: 55.766600, 37.685500");
    expect(html).toContain("https://bmstu.ru/events/register");
    expect(html).toContain("&lt;script&gt;alert(1)&lt;/script&gt;");
    expect(html).not.toContain("<script>alert(1)</script>");
  });
});
