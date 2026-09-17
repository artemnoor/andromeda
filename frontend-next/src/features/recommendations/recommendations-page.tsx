"use client";

import { useEffect, useState } from "react";
import { Sparkles, TrendingUp, TrendingDown, ArrowRight, Info, Check, CircleAlert } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { PageHeader, Loading, ErrorState, ProfileRequired, ScoreBadge, Stat, SectionTitle, Tag } from "@/components/shared";
import { getCurrentProfile, getCurrentRecommendations } from "@/lib/api";
import { formatPercent, formatShare, formatDecimal } from "@/lib/format";
import type { UserProfileSnapshot, RecommendationsResponse, Recommendation, DecisionSuggestion } from "@/lib/types";
import type { Route } from "@/lib/router";
import { useDecisionContext } from "@/features/decision/decision-context";
import { ProgramShortlistActions } from "@/features/decision/program-shortlist-actions";

export function RecommendationsPage({ navigate }: { navigate: (route: Route) => void }) {
  const {
    suggestions,
    isSuggestionsLoading,
    mutationError,
    acceptSuggestion,
    rejectSuggestion,
    refreshSuggestions,
  } = useDecisionContext();
  const [profile, setProfile] = useState<UserProfileSnapshot | null>(null);
  const [recs, setRecs] = useState<RecommendationsResponse | null>(null);
  const [legacyLoading, setLegacyLoading] = useState(false);
  const [decisionReady, setDecisionReady] = useState(false);
  const [pendingSuggestion, setPendingSuggestion] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  const loadLegacy = () => {
    setLegacyLoading(true);
    setNotFound(false);
    Promise.all([getCurrentProfile(), getCurrentRecommendations(10)])
      .then(([p, r]) => {
        setProfile(p);
        setRecs(r);
      })
      .catch(() => {
        setNotFound(true);
      })
      .finally(() => setLegacyLoading(false));
  };

  useEffect(() => {
    void refreshSuggestions().finally(() => setDecisionReady(true));
  }, [refreshSuggestions]);

  useEffect(() => {
    // A successful decision response, including an empty one, is the main
    // screen contract. Legacy recommendations are only a compatibility
    // fallback when that endpoint is unavailable.
    if (decisionReady && suggestions === null && !legacyLoading && !recs && !notFound) loadLegacy();
  }, [decisionReady, suggestions, legacyLoading, recs, notFound]);

  const accept = async (candidate: DecisionSuggestion) => {
    setPendingSuggestion(candidate.programId);
    try {
      await acceptSuggestion(candidate.programId, candidate.partition === "alternative" ? "alternative" : "primary");
      await refreshSuggestions();
    } catch {
      // The provider exposes the safe mutation error and preserves state.
    } finally {
      setPendingSuggestion(null);
    }
  };
  const reject = async (candidate: DecisionSuggestion) => {
    setPendingSuggestion(candidate.programId);
    try {
      await rejectSuggestion(candidate.programId);
      await refreshSuggestions();
    } catch {
      // The provider exposes the safe mutation error and preserves state.
    } finally {
      setPendingSuggestion(null);
    }
  };

  if (isSuggestionsLoading && !suggestions) return <Loading label="Ищем кандидатов по доступным данным…" />;
  if (suggestions) {
    return (
      <div data-testid="recommendations-page">
        <PageHeader
          eyebrow="Подобрать"
          title="Предложения системы"
          description="Это объяснимые кандидаты для вашего выбора, а не решение за вас. Admission risk, Content Fit и пробелы данных показаны отдельно."
          actions={<Button variant="outline" size="sm" onClick={() => void refreshSuggestions()} disabled={isSuggestionsLoading} className="gap-1"><Sparkles className="h-4 w-4" /> Обновить</Button>}
        />
        {mutationError && <p className="mb-4 flex items-center gap-2 rounded-lg border border-amber-300/60 bg-amber-50 px-3 py-2 text-sm text-amber-950" role="status" aria-live="polite"><CircleAlert className="h-4 w-4" />{mutationError}</p>}
        <Card className="mb-6">
          <CardContent className="grid gap-4 p-4 md:grid-cols-3">
            <Stat label="Основных кандидатов" value={suggestions.primaryCandidates.length} hint="предлагает система" />
            <Stat label="Альтернатив" value={suggestions.alternativeCandidates.length} hint="предлагает система" />
            <Stat label="Ревизия контекста" value={suggestions.contextRevision} hint="explicit choice не меняется от GET" />
          </CardContent>
        </Card>
        {suggestions.suggestions.length > 0 ? (
          <div className="space-y-3">
            {suggestions.suggestions.map((candidate) => <DecisionSuggestionCard key={candidate.programId} candidate={candidate} pending={pendingSuggestion === candidate.programId || pendingSuggestion !== null} onAccept={() => void accept(candidate)} onReject={() => void reject(candidate)} navigate={navigate} />)}
          </div>
        ) : (
          <Card className="border-dashed"><CardContent className="p-6 text-sm text-muted-foreground">Кандидаты пока не сформированы. {suggestions.missingData.length ? `Не хватает данных: ${suggestions.missingData.join(", ")}.` : "Откройте каталог или уточните предпочтения."}</CardContent></Card>
        )}
      </div>
    );
  }

  if (legacyLoading) return <Loading label="Загружаем совместимые рекомендации…" />;
  if (notFound || !profile || !recs)
    return (
      <div>
        <PageHeader eyebrow="Подобрать" title="Предложения системы" description="Сначала можно уточнить предпочтения, но это не обязательный этап для каталога, сравнения или поступления." />
        <ProfileRequired onAction={() => navigate({ view: "proftest" })} />
      </div>
    );

  return (
    <div>
      <PageHeader
        eyebrow="Подобрать · совместимость"
        title="Предложения на основе профиля"
        description={`Совместимый источник кандидатов. Уверенность профиля — ${formatPercent(profile.profile.confidence, 0)}. Добавление в shortlist всегда выполняется отдельно.`}
        actions={
          <Button variant="outline" size="sm" onClick={() => navigate({ view: "proftest" })} className="gap-1">
            <Sparkles className="h-4 w-4" /> Обновить профиль
          </Button>
        }
      />

      <Card className="mb-6">
        <CardContent className="grid gap-4 p-4 md:grid-cols-3">
          <Stat label="Программ в выдаче" value={recs.recommendations.length} />
          <Stat label="Лучший Content Fit" value={recs.recommendations[0]?.contentFit ?? "—"} />
          <Stat label="Профиль обновлён" value={new Date(profile.updatedAt).toLocaleDateString("ru-RU")} />
        </CardContent>
      </Card>

      <div className="space-y-4">
        {recs.recommendations.map((r, i) => (
          <RecommendationCard key={r.programId} rec={r} rank={i + 1} navigate={navigate} />
        ))}
      </div>
    </div>
  );
}

function DecisionSuggestionCard({
  candidate,
  pending,
  onAccept,
  onReject,
  navigate,
}: {
  candidate: DecisionSuggestion;
  pending: boolean;
  onAccept: () => void;
  onReject: () => void;
  navigate: (route: Route) => void;
}) {
  const fit = candidate.contentFit?.contentFit;
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="min-w-0">
            <p className="font-mono text-xs text-primary">{candidate.programCode}</p>
            <button type="button" onClick={() => navigate({ view: "program", id: candidate.programId })} className="mt-1 text-left font-serif text-lg font-semibold hover:text-primary">{candidate.programName}</button>
            <div className="mt-2 flex flex-wrap gap-1.5">
              <Tag tone="muted">Системное предложение</Tag>
              <Tag tone="muted">Поступление: {candidate.admissionStatus ?? candidate.admissionRisk}</Tag>
              {fit !== undefined && fit !== null && <ScoreBadge value={fit} />}
            </div>
          </div>
          <Tag tone={candidate.partition === "alternative" ? "muted" : "primary"}>{candidate.partition === "alternative" ? "Альтернатива" : "Основной кандидат"}</Tag>
        </div>
        <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
          <div><p className="mb-1 flex items-center gap-1 font-medium"><Check className="h-4 w-4 text-emerald-600" />Почему включено</p><p className="text-muted-foreground">{candidate.reasons.whyIncluded.join("; ") || "Недостаточно данных для объяснения"}</p></div>
          <div><p className="mb-1 font-medium">Что может не подойти</p><p className="text-muted-foreground">{candidate.reasons.whyMayNotFit.join("; ") || "Явных противопоказаний не найдено"}</p></div>
        </div>
        {candidate.sourceGaps.length > 0 && <p className="mt-3 text-xs text-muted-foreground">Пробелы источника: {candidate.sourceGaps.join(", ")}</p>}
        <div className="mt-4 flex flex-wrap gap-2">
          <Button type="button" size="sm" disabled={pending} onClick={onAccept}>Добавить в shortlist</Button>
          <Button type="button" size="sm" variant="outline" disabled={pending} onClick={onReject}>Не предлагать</Button>
        </div>
      </CardContent>
    </Card>
  );
}

function RecommendationCard({ rec, rank, navigate }: { rec: Recommendation; rank: number; navigate: (route: Route) => void }) {
  const [open, setOpen] = useState(false);
  const b = rec.score.breakdown;
  return (
    <Card className="overflow-hidden transition hover:shadow-md">
      <CardContent className="p-4">
        <div className="flex flex-col gap-4 md:flex-row md:items-center">
          <div className="flex items-center gap-3 md:w-56">
            <span className="font-serif text-2xl font-bold text-muted-foreground/40">#{rank}</span>
            <div className="flex flex-col">
              <ScoreBadge value={rec.contentFit} className="text-base" />
              <span className="mt-1 text-[10px] uppercase tracking-wide text-muted-foreground">Content Fit</span>
            </div>
          </div>
          <div className="min-w-0 flex-1">
            <p className="font-mono text-xs text-primary">{rec.programCode}</p>
            <button onClick={() => navigate({ view: "program", id: rec.programId })} className="text-left font-serif text-lg font-semibold leading-snug hover:text-primary">
              {rec.programName}
            </button>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {rec.distinctiveSubjects.slice(0, 3).map((s) => (
                <Tag key={s} tone="muted">{s}</Tag>
              ))}
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={() => setOpen((v) => !v)} className="gap-1">
            <Info className="h-4 w-4" /> {open ? "Скрыть" : "Подробнее"}
          </Button>
        </div>

        {open && (
          <div className="mt-4 grid gap-5 border-t border-border/60 pt-4 lg:grid-cols-2">
            <div>
              <SectionTitle>Разбивка скоринга</SectionTitle>
              <div className="space-y-2">
                <BreakdownRow label="Соответствие предметов" value={b.subjectFit} />
                <BreakdownRow label="Соответствие занятий" value={b.activityFit} />
                <BreakdownRow label="Отличительность" value={b.distinctiveFit} />
                <BreakdownRow label="Штраф за анти-интересы" value={b.antiPenalty} tone="neg" />
                <BreakdownRow label="Сырой Content Fit" value={b.rawContentFit} />
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <SectionTitle>Почему подходит</SectionTitle>
                <ul className="space-y-1.5 text-sm text-muted-foreground">
                  {rec.reasons.map((r, i) => (
                    <li key={i} className="flex gap-1.5">
                      <TrendingUp className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                      <span>{r.text}</span>
                    </li>
                  ))}
                </ul>
              </div>
              {rec.antiFitReasons.length > 0 && (
                <div>
                  <SectionTitle>Что может не подойти</SectionTitle>
                  <ul className="space-y-1.5 text-sm text-muted-foreground">
                    {rec.antiFitReasons.map((r, i) => (
                      <li key={i} className="flex gap-1.5">
                        <TrendingDown className="mt-0.5 h-4 w-4 shrink-0 text-orange-600" />
                        <span>{r.text}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="flex flex-wrap gap-2">
                {rec.admissionFit && <Tag tone="muted">Шанс поступления: {rec.admissionFit.score ?? "—"}</Tag>}
                {rec.workloadReadiness && <Tag tone="muted">Готовность к нагрузке: {rec.workloadReadiness.score ?? "—"}</Tag>}
              </div>
            </div>
          </div>
        )}
        <ProgramShortlistActions programId={rec.programId} compact />
      </CardContent>
    </Card>
  );
}

function BreakdownRow({ label, value, tone }: { label: string; value: string; tone?: "neg" }) {
  const n = Number(value);
  const pct = Math.max(0, Math.min(100, (tone === "neg" ? 1 + n : n) * 100));
  return (
    <div>
      <div className="flex justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="tabular-nums font-medium">{formatDecimal(value, 3)}</span>
      </div>
      <Progress value={pct} className="h-1.5" />
    </div>
  );
}
