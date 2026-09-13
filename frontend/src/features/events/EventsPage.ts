import { getEvents, type EventQuery } from "../../api/client";
import { ApiError } from "../../api/errors";
import type { components } from "../../api/generated";

import { renderEventsFilters, type EventsFiltersState } from "./EventsFilters";
import { renderEventsList } from "./EventsList";
import { renderEventsError, renderEventsLoading, renderEventsProfileRequired } from "./EventsStates";

type Program = components["schemas"]["ProgramSummaryResponse"];

export function renderEventsPage(root: HTMLElement, programs: readonly Program[]): void {
  root.innerHTML = `<section class="hero compact events-hero"><p class="eyebrow">Andromeda · университетские события</p><h1>События, на которые стоит прийти</h1><p class="lead">ДОД, лекции, конкурсы и карьерные встречи МГТУ с понятными датами, местами и ссылками регистрации.</p></section><div id="events-filter-root"></div><main id="events-result-root"></main>`;
  const filterRoot = root.querySelector<HTMLElement>("#events-filter-root");
  const resultRoot = root.querySelector<HTMLElement>("#events-result-root");
  if (!filterRoot || !resultRoot) return;
  let filters: EventsFiltersState = { kind: "", format: "", from: "", to: "", recommended: false };
  const submit = (next: EventsFiltersState): void => {
    filters = next;
    renderEventsFilters(filterRoot, filters, submit);
    void loadEvents(resultRoot, filters, programs);
  };
  renderEventsFilters(filterRoot, filters, submit);
  void loadEvents(resultRoot, filters, programs);
}

async function loadEvents(root: HTMLElement, filters: EventsFiltersState, programs: readonly Program[]): Promise<void> {
  renderEventsLoading(root);
  try {
    const response = await getEvents(toQuery(filters));
    renderEventsList(root, response, programs, filters.recommended);
  } catch (error: unknown) {
    if (filters.recommended && error instanceof ApiError && error.status === 404) {
      renderEventsProfileRequired(root);
      return;
    }
    const message = error instanceof ApiError ? `${error.payload.code}: ${error.payload.message}` : "Не удалось получить список событий";
    renderEventsError(root, message);
  }
}

export function toQuery(filters: EventsFiltersState): EventQuery {
  const query: EventQuery = {};
  if (filters.kind) query.kind = filters.kind;
  if (filters.format) query.format = filters.format;
  if (filters.from) query.from = localDateIso(filters.from);
  if (filters.to) query.to = localDateIso(filters.to, true);
  if (filters.recommended) query.recommended = true;
  return query;
}

function localDateIso(value: string, endOfDay = false): string {
  const time = endOfDay ? "23:59:59" : "00:00:00";
  return new Date(`${value}T${time}`).toISOString();
}
