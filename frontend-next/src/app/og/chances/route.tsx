/* eslint-disable react-hooks/error-boundaries -- route handlers convert failures to HTTP responses. */
import { OgFrame, SmallList } from "@/features/og/components";
import { PALETTES } from "@/features/og/theme";
import { statusLabel, text } from "@/features/og/format";
import { ogResponse } from "@/features/og/render";
import { fetchInternal, errorResponse, prepare } from "../shared";

export async function GET(request: Request) {
  try {
    const { context, theme } = await prepare(request, 0, 3);
    const suggestions = await fetchInternal<Record<string, unknown>>(context, "/decision/suggestions");
    const palette = PALETTES[theme];
    const source = [...(Array.isArray(suggestions.primaryCandidates) ? suggestions.primaryCandidates : []), ...(Array.isArray(suggestions.alternativeCandidates) ? suggestions.alternativeCandidates : [])].slice(0, 5) as Record<string, unknown>[];
    return ogResponse(<OgFrame theme={theme} eyebrow="Поступление" title="Реалистичность вариантов"><div style={{ display: "flex", flexDirection: "column", gap: 18 }}>{source.map((item) => { const fit = item.admissionFit as Record<string, unknown> | undefined; const score = typeof fit?.score === "number" ? fit.score : null; return <div key={String(item.programId)} style={{ display: "flex", alignItems: "center", gap: 18, fontSize: 22 }}><div style={{ display: "flex", width: 310, fontWeight: 700 }}>{text(item.programName)}</div><div style={{ flex: 1, height: 22, borderRadius: 11, background: palette.border, display: "flex" }}>{score === null ? <div style={{ display: "flex", paddingLeft: 12, color: palette.muted, fontSize: 17 }}>нет сопоставимого балла</div> : <div style={{ width: `${Math.max(4, Math.min(100, score))}%`, height: 22, borderRadius: 11, background: palette.secondary }} />}</div><div style={{ display: "flex", width: 190, color: score === null ? palette.muted : palette.secondary }}>{score === null ? statusLabel(item.admissionStatus) : `${score} · ${statusLabel(item.admissionStatus)}`}</div></div>; })}</div>{!source.length && <SmallList palette={palette} items={["добавьте баллы ЕГЭ в DecisionContext", "отсутствие данных не означает нулевой шанс"]} />}</OgFrame>, 1200, 760);
  } catch (error) {
    return errorResponse(error);
  }
}
