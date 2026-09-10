import type { CurriculumResponse } from "../../api/client";

export function renderCurriculumScreen(root: HTMLElement, response: CurriculumResponse): void {
  const rows = response.items
    .map(
      (item) => `<tr><td>${item.semester ?? "—"}</td><th scope="row">${escapeHtml(item.discipline.name)}</th><td>${item.hours}</td><td>${item.credits ?? "—"}</td><td>${item.assessmentTypes?.join(", ") ?? "—"}</td></tr>`,
    )
    .join("");
  root.innerHTML = `
    <section class="section-heading"><div><p class="eyebrow">Учебный план</p><h2>${escapeHtml(response.program.name)}</h2></div><span class="count">${response.items.length} дисциплин</span></section>
    <div class="table-wrap"><table><thead><tr><th>Семестр</th><th>Дисциплина</th><th>Часы</th><th>З.е.</th><th>Контроль</th></tr></thead><tbody>${rows}</tbody></table></div>
  `;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
