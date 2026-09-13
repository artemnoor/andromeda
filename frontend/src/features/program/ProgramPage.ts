import { getProgram } from "../../api/client";
import type { ProgramResponse } from "../../api/client";
import type { components } from "../../api/generated";
import { ApiError } from "../../api/errors";
import { renderProgramScreen } from "./ProgramScreen";

type Program = components["schemas"]["ProgramSummaryResponse"];

export function renderProgramPage(root: HTMLElement, programs: readonly Program[], requestedId?: string): void {
  if (programs.length === 0) {
    root.innerHTML = '<section class="empty-state"><h2>Программы не найдены</h2><p>API пока не вернул доступные программы.</p></section>';
    return;
  }
  const selectedId = requestedId && programs.some((program) => program.id === requestedId) ? requestedId : programs[0]?.id;
  if (!selectedId) return;
  root.innerHTML = `<section class="hero compact"><p class="eyebrow">Andromeda · программа</p><h1>Поступление и содержание</h1><p class="lead">Откройте программу и проверьте опубликованные условия поступления, связанные с её учебным планом.</p><label class="program-picker"><span>Образовательная программа</span><select data-testid="program-detail-select">${programs.map((program) => `<option value="${escapeAttribute(program.id)}" ${program.id === selectedId ? "selected" : ""}>${escapeHtml(program.code)} · ${escapeHtml(program.name)}</option>`).join("")}</select></label></section><main id="program-detail" aria-live="polite"></main>`;
  const detailElement = root.querySelector<HTMLElement>("#program-detail");
  const selectElement = root.querySelector<HTMLSelectElement>("[data-testid='program-detail-select']");
  if (!detailElement || !selectElement) return;
  const detail = detailElement;
  const select = selectElement;
  select.addEventListener("change", () => {
    const nextId = select.value;
    const nextHash = `#program/${encodeURIComponent(nextId)}`;
    if (window.location.hash === nextHash) loadProgram(nextId);
    else window.location.hash = nextHash;
  });
  loadProgram(selectedId);

  function loadProgram(id: string): void {
    detail.innerHTML = '<p class="loading">Загружаем программу из API…</p>';
    void getProgram(id).then((response: ProgramResponse) => renderProgramScreen(detail, response)).catch((error: unknown) => {
      const message = error instanceof ApiError ? `${error.payload.code}: ${error.payload.message}` : "Не удалось получить программу";
      detail.innerHTML = `<section class="error" role="alert"><p class="eyebrow">Ошибка API</p><h2>${escapeHtml(message)}</h2><p>Попробуйте выбрать программу ещё раз.</p></section>`;
    });
  }
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}

function escapeAttribute(value: string): string {
  return escapeHtml(value);
}
