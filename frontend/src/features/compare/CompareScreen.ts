import type { CompareResponse } from "../../api/client";
import type { components } from "../../api/generated";

const COMPARE_STATUS = {
  BOTH: "both",
  ONLY_A: "only_a",
  ONLY_B: "only_b",
  DIFFERENT: "different",
} as const satisfies Record<Uppercase<components["schemas"]["CompareStatus"]>, components["schemas"]["CompareStatus"]>;

export function renderCompareScreen(root: HTMLElement, response: CompareResponse): void {
  const rows = response.rows
    .map((row) => {
      const tone = row.status === COMPARE_STATUS.DIFFERENT ? COMPARE_STATUS.DIFFERENT : row.status === COMPARE_STATUS.BOTH ? COMPARE_STATUS.BOTH : "missing";
      return `<tr class="${tone}"><td>${row.semester ?? "—"}</td><th scope="row">${escapeHtml(row.discipline.name)}</th>${workloadCell(row.a)}${workloadCell(row.b)}<td><span class="status">${escapeHtml(row.status)}</span></td></tr>`;
    })
    .join("");
  root.innerHTML = `
    <section class="hero compact"><p class="eyebrow">Tracer Bullet · compare</p><h1>Учебные планы, без догадок</h1><p class="lead">Сравнение реальных программ BMSTU через один типизированный контракт.</p></section>
    <section class="compare-head"><div><span class="label">Программа A</span><strong>${escapeHtml(response.programA.code)}</strong><span>${escapeHtml(response.programA.name)}</span></div><div><span class="label">Программа B</span><strong>${escapeHtml(response.programB.code)}</strong><span>${escapeHtml(response.programB.name)}</span></div></section>
    <div class="table-wrap"><table><thead><tr><th>Семестр</th><th>Дисциплина</th><th>${escapeHtml(response.programA.code)} · часы / з.е.</th><th>${escapeHtml(response.programB.code)} · часы / з.е.</th><th>Статус</th></tr></thead><tbody>${rows}</tbody></table></div>
  `;
}

function workloadCell(workload: CompareResponse["rows"][number]["a"]): string {
  if (!workload) return "<td class=\"empty\">—</td>";
  return `<td><strong>${workload.hours} ч</strong><br><span>${workload.credits ?? "—"} з.е. · ${workload.assessmentTypes?.join(", ") ?? "контроль не указан"}</span></td>`;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
