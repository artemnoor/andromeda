import { describe, expect, it } from "vitest";

import type { PersonalRouteResponse } from "../../api/client";

import { renderPersonalRouteContent } from "./PersonalRoutePage";

const response = {
  status: "ready",
  summary: "План для интересов пользователя",
  recommendations: [{ programId: "program:09.03.01-02", programCode: "09.03.01-02", programName: "Информатика", contentFit: 92 }],
  steps: [
    { position: 1, kind: "explore_program", reason: "Разобраться в содержании", programIds: ["program:09.03.01-02"], recommendation: { programId: "program:09.03.01-02", programCode: "09.03.01-02", programName: "Информатика", contentFit: 92 }, eventId: null, event: null, venueId: null, point: null, startsAt: null },
    { position: 2, kind: "attend_event", reason: "Увидеть программу в действии", programIds: ["program:09.03.01-02"], recommendation: null, eventId: "event:bmstu:open-day", event: { id: "event:bmstu:open-day", title: "<script>alert(1)</script>", kind: "open_day", format: "offline", startsAt: "2026-10-17T11:00:00+03:00", endsAt: null, description: "Описание", registrationUrl: "https://bmstu.ru/register", universityIds: ["university:bmstu"], departmentIds: [], programIds: ["program:09.03.01-02"], venue: { id: "venue:bmstu:main-campus", name: "Главный корпус", address: "Москва", latitude: "55.7666", longitude: "37.6855" }, provenance: [] }, venueId: "venue:bmstu:main-campus", point: { id: "venue:bmstu:main-campus", pointType: "building", name: "Главный корпус", address: "Москва", latitude: "55.7666", longitude: "37.6855", universityIds: ["university:bmstu"], departmentIds: [], programIds: ["program:09.03.01-02"], eventCount: 1, provenance: [], universities: [], departments: [], programs: [] }, startsAt: "2026-10-17T11:00:00+03:00" },
  ],
} as unknown as PersonalRouteResponse;

describe("personal route page", () => {
  it("renders logical steps, canonical IDs, event data, and safe external links", () => {
    const html = renderPersonalRouteContent(response, [{ id: "program:09.03.01-02", directionId: "direction:09.03.01", code: "09.03.01-02", name: "Информатика", educationYear: 2026, studyPlanUrl: "https://bmstu.ru/plan.pdf", sourceUrl: "https://bmstu.ru/program" }]);

    expect(html).toContain("Разобраться в программе");
    expect(html).toContain("Главный корпус");
    expect(html).toContain("event:bmstu:open-day");
    expect(html).toContain("https://bmstu.ru/register");
    expect(html).not.toContain("<script>alert(1)</script>");
  });
});
