import type { CompareResponse } from "../../api/client";

export function renderCompareTable(response: CompareResponse): string {
  const rows = response.rows.map((row) => {
    const tone = row.status === "different" ? "different" : row.status === "both" ? "same" : "missing";
    const areas = row.discipline.areaWeights.map((area) => `${escapeHtml(area.name)} · ${formatPercent(area.weight)}`).join("<br>");
    return `<tr class="${tone}"><td>${row.semester ?? "—"}</td><th scope="row">${escapeHtml(row.discipline.name)}<small class="area-hint">${areas}</small></th>${workloadCell(row.a)}${workloadCell(row.b)}<td><strong>${row.hoursDelta ?? "—"} ч</strong><br><span>${row.creditsDelta ?? "—"} ЗЕТ</span></td><td><span class="status">${escapeHtml(row.status)}</span></td></tr>`;
  }).join("");
  if (!rows) return `<p class="empty">Для выбранного семестра дисциплины не найдены.</p>`;
  return `<div class="table-wrap" data-testid="comparison-table"><table><thead><tr><th>Семестр</th><th>Дисциплина</th><th>${escapeHtml(response.programA.code)}<br>часы / ЗЕТ</th><th>${escapeHtml(response.programB.code)}<br>часы / ЗЕТ</th><th>Δ A − B</th><th>Статус</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

export function renderAreaBreakdowns(response: CompareResponse): string {
  return `<div class="area-grid" data-testid="area-breakdown">${areaBreakdownCard("A", response.areaBreakdownA)}${areaBreakdownCard("B", response.areaBreakdownB)}</div>`;
}

function workloadCell(workload: CompareResponse["rows"][number]["a"]): string {
  if (!workload) return "<td class=\"empty\">—</td>";
  return `<td><strong>${workload.hours} ч</strong><br><span>${workload.credits ?? "—"} ЗЕТ · ${workload.assessmentTypes?.join(", ") ?? "контроль не указан"}</span></td>`;
}

function areaBreakdownCard(label: string, areas: CompareResponse["areaBreakdownA"]): string {
  const rows = areas.map((area) => {
    const percent = formatPercent(area.share);
    const width = Math.max(0, Math.min(100, Number(area.share) * 100));
    return `<li><div><span>${escapeHtml(area.name)}</span><strong>${percent}</strong></div><span class="area-bar"><i style="width:${width}%"></i></span></li>`;
  }).join("");
  return `<article class="area-card"><span class="label">Программа ${label}</span><ul>${rows || "<li class=\"empty\">Нет классифицированной нагрузки</li>"}</ul></article>`;
}

function formatPercent(value: string): string {
  const percent = Number(value) * 100;
  return Number.isFinite(percent) ? `${percent.toFixed(1)}%` : "—";
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
