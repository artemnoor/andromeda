"use client";

import { useEffect, useState } from "react";
import { Workflow, Compass, Sparkles, Route, ArrowRight, CheckCircle2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PageHeader, Loading, ErrorState, ScoreBadge, Tag, SectionTitle } from "@/components/shared";
import { getCurrentProfile, getCurrentRecommendations, getPersonalRoute } from "@/lib/api";
import { formatPercent } from "@/lib/format";
import type { UserProfileSnapshot, RecommendationsResponse, PersonalRouteResponse } from "@/lib/types";
import type { Route as RouteType } from "@/lib/router";

type Phase = "intro" | "profile" | "recommendations" | "route";

export function UnifiedFlowPage({ navigate }: { navigate: (route: RouteType) => void }) {
  const [phase, setPhase] = useState<Phase>("intro");
  const [profile, setProfile] = useState<UserProfileSnapshot | null>(null);
  const [recs, setRecs] = useState<RecommendationsResponse | null>(null);
  const [route, setRoute] = useState<PersonalRouteResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const runPhase = async (p: Phase) => {
    setLoading(true);
    try {
      if (p === "profile") {
        const prof = await getCurrentProfile();
        setProfile(prof);
      } else if (p === "recommendations") {
        const [prof, r] = await Promise.all([getCurrentProfile(), getCurrentRecommendations(10)]);
        setProfile(prof);
        setRecs(r);
      } else if (p === "route") {
        const [prof, r, rt] = await Promise.all([getCurrentProfile(), getCurrentRecommendations(10), getPersonalRoute(10)]);
        setProfile(prof);
        setRecs(r);
        setRoute(rt);
      }
      setPhase(p);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="Единый путь"
        title="Сценарий абитуриента"
        description="Связанный поток: профиль → рекомендации → личный маршрут. Один экран показывает, как данные перетекают между этапами выбора программы."
      />

      <div className="mb-6 flex flex-wrap items-center gap-2">
        {(["intro", "profile", "recommendations", "route"] as Phase[]).map((p, i) => {
          const labels = ["Старт", "Профиль", "Рекомендации", "Маршрут"];
          const done = phase === p || (["intro", "profile", "recommendations", "route"].indexOf(phase) > i);
          const active = phase === p;
          return (
            <div key={p} className="flex items-center gap-2">
              <button
                onClick={() => runPhase(p)}
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition ${
                  active ? "bg-primary text-primary-foreground" : done ? "bg-accent text-accent-foreground" : "bg-muted text-muted-foreground"
                }`}
              >
                {done && !active ? <CheckCircle2 className="h-4 w-4" /> : <span className="grid h-4 w-4 place-items-center text-xs">{i + 1}</span>}
                {labels[i]}
              </button>
              {i < 3 && <ArrowRight className="h-3.5 w-3.5 text-muted-foreground/50" />}
            </div>
          );
        })}
      </div>

      {loading && <Loading label="Загружаем этап…" />}

      {!loading && phase === "intro" && (
        <Card>
          <CardContent className="flex flex-col items-start gap-4 p-6">
            <div className="flex items-center gap-2">
              <Workflow className="h-6 w-6 text-primary" />
              <h2 className="font-serif text-xl font-semibold">Как это работает</h2>
            </div>
            <p className="max-w-2xl text-sm text-muted-foreground">
              Andromeda собирает разрозненные данные об образовательных программах в одну объяснимую модель.
              Этот экран показывает полный путь абитуриента за четыре шага — от профиля интересов до конкретного плана действий.
            </p>
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                { icon: Compass, t: "Профиль", d: "Интересы и веса предметных областей" },
                { icon: Sparkles, t: "Рекомендации", d: "Топ программ с разбивкой скоринга" },
                { icon: Route, t: "Маршрут", d: "Пошаговый план: изучить, сравнить, посетить" },
              ].map((s) => (
                <div key={s.t} className="rounded-xl border border-border/60 bg-card p-4">
                  <s.icon className="mb-2 h-5 w-5 text-primary" />
                  <p className="font-semibold">{s.t}</p>
                  <p className="text-xs text-muted-foreground">{s.d}</p>
                </div>
              ))}
            </div>
            <Button onClick={() => runPhase("profile")} className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
              Начать <ArrowRight className="h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      )}

      {!loading && phase === "profile" && profile && (
        <Card>
          <CardContent className="p-5">
            <SectionTitle hint={`уверенность ${formatPercent(profile.profile.confidence, 0)}`}>Профиль интересов</SectionTitle>
            <div className="space-y-2">
              {profile.profile.preferredSubjectWeights.map((w) => (
                <div key={w.code} className="flex items-center gap-3">
                  <span className="w-48 text-sm">{w.code}</span>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                    <div className="h-full bg-primary" style={{ width: `${Number(w.weight) * 100}%` }} />
                  </div>
                  <span className="w-12 text-right text-sm tabular-nums text-muted-foreground">{formatPercent(w.weight, 0)}</span>
                </div>
              ))}
            </div>
            <Button className="mt-4 gap-2 bg-primary text-primary-foreground hover:bg-primary/90" onClick={() => runPhase("recommendations")}>
              К рекомендациям <ArrowRight className="h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      )}

      {!loading && phase === "recommendations" && recs && (
        <div className="space-y-3">
          <SectionTitle hint={`${recs.recommendations.length} программ`}>Топ рекомендаций</SectionTitle>
          {recs.recommendations.slice(0, 5).map((r, i) => (
            <Card key={r.programId}>
              <CardContent className="flex items-center gap-4 p-4">
                <span className="font-serif text-xl font-bold text-muted-foreground/40">#{i + 1}</span>
                <ScoreBadge value={r.contentFit} />
                <div className="min-w-0 flex-1">
                  <p className="font-mono text-xs text-primary">{r.programCode}</p>
                  <button onClick={() => navigate({ view: "program", id: r.programId })} className="text-left font-semibold hover:text-primary">
                    {r.programName}
                  </button>
                </div>
                <Tag tone="muted">{r.distinctiveSubjects[0]}</Tag>
              </CardContent>
            </Card>
          ))}
          <Button className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90" onClick={() => runPhase("route")}>
            Построить маршрут <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      {!loading && phase === "route" && route && (
        <div className="space-y-3">
          <SectionTitle hint={route.summary ? "готов" : ""}>Личный маршрут</SectionTitle>
          {route.steps.map((s) => (
            <Card key={s.position}>
              <CardContent className="p-4">
                <p className="text-xs font-bold uppercase tracking-wide text-primary">Шаг {s.position}</p>
                <p className="mt-1 text-sm text-muted-foreground">{s.reason}</p>
                {s.recommendation && (
                  <Button variant="outline" size="sm" className="mt-2" onClick={() => navigate({ view: "program", id: s.recommendation!.programId })}>
                    {s.recommendation.programCode}
                  </Button>
                )}
                {s.event && (
                  <Button variant="outline" size="sm" className="mt-2 ml-2" onClick={() => navigate({ view: "event", id: s.event!.id })}>
                    {s.event.title}
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
