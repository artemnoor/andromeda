import type { CompareResponse } from "../../api/client";

export function renderCompareTable(response: CompareResponse): string {
  const rows = response.rows.map((row) => {
    const tone = row.status === "different" ? "different" : row.status === "both" ? "same" : "missing";
    return `<tr class="${tone}"><td>${row.semester ?? "—"}</td><th scope="row">${escapeHtml(row.discipline.name)}<small>${escapeHtml(row.subjectGroup ?? "Без блока")}</small></th>${workloadCell(row.a)}${workloadCell(row.b)}<td><strong>${row.hoursDelta ?? "—"} ч</strong><br><span>${row.creditsDelta ?? "—"} ЗЕТ</span></td><td><span class="status">${escapeHtml(row.status)}</span></td></tr>`;
  }).join("");
  if (!rows) return `<p class="empty">Для выбранного семестра дисциплины не найдены.</p>`;
  return `<div class="table-wrap" data-testid="comparison-table"><table><thead><tr><th>Семестр</th><th>Дисциплина · блок</th><th>${escapeHtml(response.programA.code)}<br>часы / ЗЕТ</th><th>${escapeHtml(response.programB.code)}<br>часы / ЗЕТ</th><th>Δ A − B</th><th>Статус</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

export function renderBlockSummary(response: CompareResponse): string {
  return response.blocks.map((block) => `<article class="block-card"><span class="label">${escapeHtml(block.name)}</span><strong>${block.totalsA.hours} / ${block.totalsB.hours} ч</strong><span>${block.totalsA.credits} / ${block.totalsB.credits} ЗЕТ · Δ ${block.hoursDelta} ч</span></article>`).join("");
}

function workloadCell(workload: CompareResponse["rows"][number]["a"]): string {
  if (!workload) return "<td class=\"empty\">—</td>";
  return `<td><strong>${workload.hours} ч</strong><br><span>${workload.credits ?? "—"} ЗЕТ · ${workload.assessmentTypes?.join(", ") ?? "контроль не указан"}</span></td>`;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
