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
  const rows = mergeAreaBreakdowns(response.areaBreakdownA, response.areaBreakdownB);
  return `<div class="area-grid" data-testid="area-breakdown">${areaPieCard("A", response.programA.code, rows, "shareA")}${areaPieCard("B", response.programB.code, rows, "shareB")}</div>`;
}

function workloadCell(workload: CompareResponse["rows"][number]["a"]): string {
  if (!workload) return "<td class=\"empty\">—</td>";
  return `<td><strong>${workload.hours} ч</strong><br><span>${workload.credits ?? "—"} ЗЕТ · ${workload.assessmentTypes?.join(", ") ?? "контроль не указан"}</span></td>`;
}

type AreaComparisonRow = {
  code: string;
  name: string;
  shareA: number;
  shareB: number;
  color: string;
};

const AREA_COLORS: Record<string, string> = {
  mathematics_statistics: "#c2410c",
  computer_science_data: "#0f766e",
  physics_astronomy: "#2563eb",
  chemistry_materials: "#a16207",
  biology_biotechnology: "#16a34a",
  earth_environment: "#0891b2",
  engineering_technology: "#7c3aed",
  architecture_construction: "#be185d",
  agriculture_veterinary: "#65a30d",
  medicine_health: "#dc2626",
  psychology_cognitive: "#db2777",
  society_social_sciences: "#0369a1",
  economics_finance: "#92400e",
  business_management: "#9333ea",
  law_policy_public_administration: "#b91c1c",
  languages_linguistics_literature: "#0e7490",
  history_philosophy_humanities: "#57534e",
  art_design_media: "#e11d48",
  education_pedagogy: "#4f46e5",
  sport_tourism_hospitality: "#ea580c",
  safety_defense_transport: "#334155",
  universal_interdisciplinary: "#64748b",
};

const FALLBACK_AREA_COLORS = ["#7c3aed", "#0f766e", "#c2410c", "#2563eb", "#be185d"];

function areaColor(code: string): string {
  const explicitColor = AREA_COLORS[code];
  if (explicitColor) return explicitColor;

  let hash = 0;
  for (const character of code) hash = (hash * 31 + character.charCodeAt(0)) >>> 0;
  return FALLBACK_AREA_COLORS[hash % FALLBACK_AREA_COLORS.length] ?? "#64748b";
}

function areaShare(value: string | number | null | undefined): number {
  const parsed = typeof value === "number" ? value : Number(value ?? 0);
  return Number.isFinite(parsed) ? Math.max(0, Math.min(1, parsed)) : 0;
}

function mergeAreaBreakdowns(
  areaBreakdownA: CompareResponse["areaBreakdownA"],
  areaBreakdownB: CompareResponse["areaBreakdownB"],
): AreaComparisonRow[] {
  const merged = new Map<string, AreaComparisonRow>();

  for (const item of areaBreakdownA) {
    const current = merged.get(item.area) ?? { code: item.area, name: item.name, shareA: 0, shareB: 0, color: areaColor(item.area) };
    merged.set(item.area, { ...current, name: current.name || item.name, shareA: areaShare(item.share) });
  }
  for (const item of areaBreakdownB) {
    const current = merged.get(item.area) ?? { code: item.area, name: item.name, shareA: 0, shareB: 0, color: areaColor(item.area) };
    merged.set(item.area, { ...current, name: current.name || item.name, shareB: areaShare(item.share) });
  }

  return [...merged.values()].sort((left, right) => {
    const totalDelta = right.shareA + right.shareB - left.shareA - left.shareB;
    return totalDelta || left.name.localeCompare(right.name, "ru");
  });
}

function pieGradient(rows: readonly AreaComparisonRow[], shareKey: "shareA" | "shareB"): string {
  const total = rows.reduce((sum, row) => sum + row[shareKey], 0);
  if (total <= 0) return "conic-gradient(#e7e5e4 0 100%)";

  let cursor = 0;
  const segments = rows.flatMap((row) => {
    const value = row[shareKey];
    if (value <= 0) return [];
    const start = (cursor / total) * 100;
    cursor += value;
    const end = (cursor / total) * 100;
    return [`${row.color} ${start.toFixed(4)}% ${end.toFixed(4)}%`];
  });
  return `conic-gradient(${segments.join(", ")})`;
}

function areaPieCard(
  label: string,
  programCode: string,
  rows: readonly AreaComparisonRow[],
  shareKey: "shareA" | "shareB",
): string {
  const total = rows.reduce((sum, row) => sum + row[shareKey], 0);
  const legend = rows.map((row) => `<li><span class="area-legend-name"><i class="area-legend-swatch" style="background-color:${row.color}" aria-hidden="true"></i><span title="${escapeHtml(row.name)}">${escapeHtml(row.name)}</span></span><strong>${formatPercent(row[shareKey])}</strong></li>`).join("");
  const pieLabel = `Круговая диаграмма содержания программы ${label}`;
  return `<article class="area-card" data-testid="area-pie-${label.toLowerCase()}"><div class="area-card-heading"><div><span class="label">Программа ${label}</span><code>${escapeHtml(programCode)}</code></div><span class="area-card-badge">по часам</span></div><div class="area-pie-layout"><div class="area-pie" role="img" aria-label="${pieLabel}" style="background:${pieGradient(rows, shareKey)}"><div class="area-pie-center"><strong>${total > 0 ? formatPercent(total) : "—"}</strong><span>учебной нагрузки</span></div></div><ul class="area-legend" aria-label="Легенда программы ${label}">${legend || "<li class=\"empty\">Нет классифицированной нагрузки</li>"}</ul></div></article>`;
}

function formatPercent(value: string | number): string {
  const percent = Number(value) * 100;
  return Number.isFinite(percent) ? `${percent.toFixed(1)}%` : "—";
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
