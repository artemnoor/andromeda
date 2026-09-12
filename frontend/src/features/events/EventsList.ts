import type { EventListResponse } from "../../api/client";
import type { components } from "../../api/generated";

import { renderEventCard } from "./EventsCard";
import { renderEventsEmpty } from "./EventsStates";

type Program = components["schemas"]["ProgramSummaryResponse"];

export function renderEventsList(root: HTMLElement, response: EventListResponse, programs: readonly Program[], recommended: boolean): void {
  if (response.items.length === 0) {
    renderEventsEmpty(root, recommended);
    return;
  }
  root.innerHTML = `<section class="events-results" data-testid="events-results"><div class="section-heading"><div><p class="eyebrow">Календарь университета</p><h2>Ближайшие события</h2></div><span class="count" data-testid="events-count">${response.total} событий</span></div><div class="events-grid">${response.items.map((event) => renderEventCard(event, programs)).join("")}</div></section>`;
}
