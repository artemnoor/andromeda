import type { components } from "../../api/generated";

type Program = components["schemas"]["ProgramSummaryResponse"];

export type CompareSelection = {
  programA: string;
  programB: string;
  scope: components["schemas"]["ComparisonScope"];
  semester?: number;
};

export function renderProgramSelectors(
  root: HTMLElement,
  programs: readonly Program[],
  selection: CompareSelection,
  onSubmit: (selection: CompareSelection) => void,
): void {
  root.innerHTML = `
    <form class="compare-controls" aria-label="Параметры сравнения">
      <label><span>Программа A</span><select data-testid="program-a" name="programA">${options(programs, selection.programA)}</select></label>
      <label><span>Программа B</span><select data-testid="program-b" name="programB">${options(programs, selection.programB)}</select></label>
      <label><span>Охват</span><select data-testid="comparison-scope" name="scope"><option value="all" ${selection.scope === "all" ? "selected" : ""}>Всё обучение</option><option value="semester" ${selection.scope === "semester" ? "selected" : ""}>Семестр</option></select></label>
      <label class="semester-control"><span>Семестр</span><select data-testid="comparison-semester" name="semester" ${selection.scope === "all" ? "disabled" : ""}>${semesterOptions(selection.semester)}</select></label>
      <button data-testid="compare-submit" type="submit">Сравнить</button>
    </form>
  `;
  const form = root.querySelector<HTMLFormElement>("form");
  const scope = form?.elements.namedItem("scope") as HTMLSelectElement | null;
  const semester = form?.elements.namedItem("semester") as HTMLSelectElement | null;
  scope?.addEventListener("change", () => {
    if (semester) semester.disabled = scope.value === "all";
  });
  form?.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    onSubmit({
      programA: String(data.get("programA")),
      programB: String(data.get("programB")),
      scope: data.get("scope") as CompareSelection["scope"],
      semester: Number(data.get("semester") ?? 1),
    });
  });
}

function options(programs: readonly Program[], selected: string): string {
  return programs.map((program) => `<option value="${escapeHtml(program.id)}" ${program.id === selected ? "selected" : ""}>${escapeHtml(program.code)} · ${escapeHtml(program.name)}</option>`).join("");
}

function semesterOptions(selected = 1): string {
  return Array.from({ length: 12 }, (_, index) => index + 1).map((semester) => `<option value="${semester}" ${semester === selected ? "selected" : ""}>${semester}</option>`).join("");
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
