import { describe, expect, it } from "vitest";

import { renderEventsFilters, type EventsFiltersState } from "./EventsFilters";

function fakeRoot(): HTMLElement {
  return { innerHTML: "", querySelector: () => null } as unknown as HTMLElement;
}

describe("event filters", () => {
  it("renders strict filter controls and preserves the selected state", () => {
    const root = fakeRoot();
    const state: EventsFiltersState = { kind: "additional_education", format: "offline", from: "2026-10-01", to: "2026-10-31", recommended: true };
    renderEventsFilters(root, state, () => undefined);
    expect(root.innerHTML).toContain('data-testid="events-kind"');
    expect(root.innerHTML).toContain('value="additional_education" selected');
    expect(root.innerHTML).toContain('value="offline" selected');
    expect(root.innerHTML).toContain('data-testid="events-recommended" type="checkbox" checked');
  });
});
