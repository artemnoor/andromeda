"use client";

import { useEffect, useState } from "react";
import { Sparkles, TrendingUp, TrendingDown, ArrowRight, Info } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { PageHeader, Loading, ErrorState, ProfileRequired, ScoreBadge, Stat, SectionTitle, Tag } from "@/components/shared";
import { getCurrentProfile, getCurrentRecommendations } from "@/lib/api";
import { taxonomyLabel } from "@/lib/labels";
import { formatPercent, formatShare, formatDecimal } from "@/lib/format";
import type { UserProfileSnapshot, RecommendationsResponse, Recommendation } from "@/lib/types";
import type { Route } from "@/lib/router";

export function RecommendationsPage({ navigate }: { navigate: (route: Route) => void }) {
  const [profile, setProfile] = useState<UserProfileSnapshot | null>(null);
  const [recs, setRecs] = useState<RecommendationsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    setNotFound(false);
    Promise.all([getCurrentProfile(), getCurrentRecommendations(10)])
      .then(([p, r]) => {
        setProfile(p);
        setRecs(r);
      })
      .catch(() => {
        setNotFound(true);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  if (loading) return <Loading label="Загружаем профиль и рекомендации…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (notFound || !profile || !recs)
    return (
      <div>
        <PageHeader eyebrow="Рекомендации" title="Персональные рекомендации" />
        <ProfileRequired onAction={() => navigate({ view: "proftest" })} />
      </div>
    );

  return (
    <div>
      <PageHeader
        eyebrow="Рекомендации"
        title="Персональные рекомендации"
        description={`Объяснимое ранжирование на основе вашего профиля. Уверенность профиля — ${formatPercent(profile.profile.confidence, 0)}.`}
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
