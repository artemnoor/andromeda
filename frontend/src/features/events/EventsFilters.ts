import type { components } from "../../api/generated";

export type EventsFiltersState = {
  kind: components["schemas"]["EventKind"] | "";
  format: components["schemas"]["EventFormat"] | "";
  from: string;
  to: string;
  recommended: boolean;
  programId?: string;
};

type FilterSubmit = (state: EventsFiltersState) => void;
type Program = components["schemas"]["ProgramSummaryResponse"];

const kindOptions: readonly [components["schemas"]["EventKind"] | "", string][] = [
  ["", "Все типы"],
  ["additional_education", "ДОД / дополнительное образование"],
  ["open_day", "День открытых дверей"],
  ["lecture", "Лекция"],
  ["competition", "Конкурс"],
  ["career", "Карьерное событие"],
  ["other", "Другое"],
];

const formatOptions: readonly [components["schemas"]["EventFormat"] | "", string][] = [
  ["", "Любой формат"],
  ["offline", "Очно"],
  ["online", "Онлайн"],
  ["hybrid", "Гибридный"],
];

export function renderEventsFilters(root: HTMLElement, state: EventsFiltersState, onSubmit: FilterSubmit, programs: readonly Program[] = []): void {
  root.innerHTML = `<form class="events-filters" data-testid="events-filters"><label><span>Тип</span><select name="kind" data-testid="events-kind">${kindOptions.map(([value, label]) => `<option value="${value}"${state.kind === value ? " selected" : ""}>${label}</option>`).join("")}</select></label><label><span>Формат</span><select name="format" data-testid="events-format">${formatOptions.map(([value, label]) => `<option value="${value}"${state.format === value ? " selected" : ""}>${label}</option>`).join("")}</select></label><label><span>Программа</span><select name="programId" data-testid="events-program"><option value="">Все программы</option>${programs.map((program) => `<option value="${escapeHtml(program.id)}"${state.programId === program.id ? " selected" : ""}>${escapeHtml(program.code)} · ${escapeHtml(program.name)}</option>`).join("")}</select></label><label><span>С</span><input name="from" data-testid="events-from" type="date" value="${escapeHtml(state.from)}"></label><label><span>По</span><input name="to" data-testid="events-to" type="date" value="${escapeHtml(state.to)}"></label><label class="events-recommended-toggle"><input name="recommended" data-testid="events-recommended" type="checkbox"${state.recommended ? " checked" : ""}><span>Только рекомендованные</span></label><button class="primary-button" data-testid="events-apply" type="submit">Показать</button></form>`;
  const form = root.querySelector<HTMLFormElement>("[data-testid='events-filters']");
  if (!form) return;
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const next: EventsFiltersState = {
      kind: (data.get("kind") as EventsFiltersState["kind"]) ?? "",
      format: (data.get("format") as EventsFiltersState["format"]) ?? "",
      from: String(data.get("from") ?? ""),
      to: String(data.get("to") ?? ""),
      recommended: data.get("recommended") === "on",
      programId: String(data.get("programId") ?? ""),
    };
    if (import.meta.env.DEV && import.meta.env.VITE_LOG_LEVEL === "DEBUG") console.debug("[events] filter_change", { recommended: next.recommended, hasDateWindow: Boolean(next.from || next.to) });
    onSubmit(next);
  });
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
