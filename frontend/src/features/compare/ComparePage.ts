import { comparePrograms, type CompareResponse } from "../../api/client";
import type { components } from "../../api/generated";
import { ApiError } from "../../api/errors";
import { renderProgramSelectors, type CompareSelection } from "../programs/ProgramSelectors";
import { renderAreaBreakdowns, renderCompareTable } from "./CompareTable";
import { renderEmpty, renderError, renderLoading } from "./CompareStates";

type Program = components["schemas"]["ProgramSummaryResponse"];

export function renderComparePage(root: HTMLElement, programs: readonly Program[]): void {
  if (programs.length < 2) {
    renderEmpty(root, "Нужно минимум две программы");
    return;
  }
  const first = programs[0];
  const second = programs[1];
  if (!first || !second) {
    renderEmpty(root, "Нужно минимум две программы");
    return;
  }
  let selection: CompareSelection = { programA: first.id, programB: second.id, scope: "all", semester: 1 };
  root.innerHTML = `<section class="hero compact"><p class="eyebrow">Andromeda · сравнение образовательных программ</p><h1>Учебные планы, без догадок</h1><p class="lead">Выберите две реальные программы МГТУ и сравните дисциплины, часы, ЗЕТ и формы контроля.</p></section><div id="compare-controls"></div><main id="comparison-result"></main>`;
  const controls = root.querySelector<HTMLElement>("#compare-controls");
  const result = root.querySelector<HTMLElement>("#comparison-result");
  if (!controls || !result) return;

  const submit = (next: CompareSelection): void => {
    selection = next;
    renderProgramSelectors(controls, programs, selection, submit);
    void loadComparison(result, selection);
  };
  renderProgramSelectors(controls, programs, selection, submit);
  void loadComparison(result, selection);
}

async function loadComparison(root: HTMLElement, selection: CompareSelection): Promise<void> {
  if (selection.programA === selection.programB) {
    renderError(root, "Выберите разные программы");
    return;
  }
  renderLoading(root);
  try {
    const response = await comparePrograms([selection.programA, selection.programB], { scope: selection.scope, semester: selection.scope === "semester" ? selection.semester : undefined });
    renderComparison(root, response);
  } catch (error: unknown) {
    const message = error instanceof ApiError ? `${error.payload.code}: ${error.payload.message}` : "Не удалось получить сравнение";
    renderError(root, message);
  }
}

function renderComparison(root: HTMLElement, response: CompareResponse): void {
  root.innerHTML = `<section class="compare-head"><div><span class="label">Программа A</span><strong>${escapeHtml(response.programA.code)}</strong><span>${escapeHtml(response.programA.name)}</span></div><div><span class="label">Программа B</span><strong>${escapeHtml(response.programB.code)}</strong><span>${escapeHtml(response.programB.name)}</span></div></section><section class="summary-grid"><article class="card"><span class="label">Итого A</span><strong>${response.totalsA.hours} ч · ${response.totalsA.credits} ЗЕТ</strong></article><article class="card"><span class="label">Итого B</span><strong>${response.totalsB.hours} ч · ${response.totalsB.credits} ЗЕТ</strong></article></section><section class="section-heading"><div><p class="eyebrow">Andromeda taxonomy</p><h2>Вектор содержания</h2></div><span class="count">Доля рассчитана по часам учебного плана</span></section>${renderAreaBreakdowns(response)}<section class="section-heading"><div><p class="eyebrow">Детали</p><h2>Сопоставление дисциплин</h2></div><span class="count">${response.rows.length} позиций</span></section>${renderCompareTable(response)}`;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
