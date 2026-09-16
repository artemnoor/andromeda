"use client";

import { useEffect, useState } from "react";
import { Route, Compass, GitCompare, CalendarDays, ArrowRight, MapPin } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PageHeader, Loading, ErrorState, ProfileRequired, EmptyState, ScoreBadge, Tag } from "@/components/shared";
import { getPersonalRoute } from "@/lib/api";
import { STEP_KIND_LABELS, ROUTE_STATUS_LABELS } from "@/lib/labels";
import { formatDateTime } from "@/lib/format";
import type { PersonalRouteResponse } from "@/lib/types";
import type { Route as RouteType } from "@/lib/router";

const STEP_ICON: Record<string, React.ComponentType<{ className?: string }>> = {
  explore_program: Compass,
  compare_programs: GitCompare,
  attend_event: CalendarDays,
};

export function PersonalRoutePage({ navigate }: { navigate: (route: RouteType) => void }) {
  const [data, setData] = useState<PersonalRouteResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    getPersonalRoute()
      .then(setData)
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loading label="Строим личный маршрут…" />;
  if (notFound)
    return (
      <div>
        <PageHeader eyebrow="Мой план" title="Личный маршрут" />
        <ProfileRequired onAction={() => navigate({ view: "proftest" })} />
      </div>
    );
  if (!data) return null;

  if (data.status === "no_recommendations" || data.steps.length === 0)
    return (
      <div>
        <PageHeader eyebrow="Мой план" title="Личный маршрут" />
        <EmptyState
          title={ROUTE_STATUS_LABELS[data.status]}
          message="Пройдите профтест, чтобы получить рекомендации и построить пошаговый план действий."
          action={<Button onClick={() => navigate({ view: "proftest" })} className="bg-primary text-primary-foreground hover:bg-primary/90">Пройти тест</Button>}
        />
      </div>
    );

  return (
    <div>
      <PageHeader
        eyebrow="Мой план"
        title="Личный маршрут"
        description={data.summary}
        actions={<Tag tone="primary">{ROUTE_STATUS_LABELS[data.status]}</Tag>}
      />

      <div className="relative space-y-4 before:absolute before:left-[19px] before:top-2 before:h-[calc(100%-2rem)] before:w-0.5 before:bg-border/70">
        {data.steps.map((step) => {
          const Icon = STEP_ICON[step.kind] ?? Route;
          return (
            <Card key={step.position} className="relative ml-12">
              <span className="absolute -left-[3.25rem] top-5 grid h-10 w-10 place-items-center rounded-full bg-primary text-primary-foreground shadow-sm">
                <Icon className="h-5 w-5" />
              </span>
              <CardContent className="p-5">
                <div className="mb-2 flex items-center gap-2">
                  <span className="text-xs font-bold uppercase tracking-wide text-primary">
                    Шаг {step.position} · {STEP_KIND_LABELS[step.kind]}
                  </span>
                </div>
                <p className="mb-3 text-sm text-muted-foreground">{step.reason}</p>

                {step.recommendation && (
                  <div className="mb-3 flex items-center gap-3 rounded-lg border border-border/60 bg-card p-3">
                    <ScoreBadge value={step.recommendation.contentFit} />
                    <div className="min-w-0">
                      <p className="font-mono text-xs text-primary">{step.recommendation.programCode}</p>
                      <button onClick={() => navigate({ view: "program", id: step.recommendation!.programId })} className="text-left font-semibold hover:text-primary">
                        {step.recommendation.programName}
                      </button>
                    </div>
                  </div>
                )}

                {step.event && (
                  <div className="mb-3 rounded-lg border border-border/60 bg-card p-3">
                    <button onClick={() => navigate({ view: "event", id: step.event!.id })} className="text-left font-semibold hover:text-primary">
                      {step.event!.title}
                    </button>
                    <p className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
                      <CalendarDays className="h-3 w-3" /> {formatDateTime(step.event?.startsAt ?? "")}
                      {step.venue?.name && <><MapPin className="ml-2 h-3 w-3" /> {step.venue.name}</>}
                    </p>
                  </div>
                )}

                <div className="flex flex-wrap gap-2">
                  {step.kind === "explore_program" && step.programIds[0] && (
                    <Button size="sm" className="gap-1 bg-primary text-primary-foreground hover:bg-primary/90" onClick={() => navigate({ view: "program", id: step.programIds[0] })}>
                      Открыть программу <ArrowRight className="h-4 w-4" />
                    </Button>
                  )}
                  {step.kind === "compare_programs" && (
                    <Button size="sm" className="gap-1 bg-primary text-primary-foreground hover:bg-primary/90" onClick={() => navigate({ view: "compare" })}>
                      Сравнить <ArrowRight className="h-4 w-4" />
                    </Button>
                  )}
                  {step.kind === "attend_event" && step.event && (
                    <Button size="sm" variant="outline" onClick={() => step.event && navigate({ view: "event", id: step.event.id })}>
                      Подробнее о событии
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
