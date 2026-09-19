"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarDays, MapPin, Video, MonitorPlay, ArrowRight, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { PageHeader, Loading, ErrorState, EmptyState, Tag } from "@/components/shared";
import { getEvents } from "@/lib/api";
import { eventKindLabel, eventFormatLabel } from "@/lib/labels";
import { formatDateTime, relativeTime } from "@/lib/format";
import type { EventItem, EventListResponse } from "@/lib/types";
import type { Route } from "@/lib/router";
import { cn } from "@/lib/utils";
import { ProgramShortlistActions } from "@/features/decision/program-shortlist-actions";

const KINDS = ["open_day", "lecture", "competition", "career", "additional_education", "other"];
const FORMATS = ["offline", "online", "hybrid"];

const FORMAT_ICON: Record<string, React.ComponentType<{ className?: string }>> = {
  offline: MapPin,
  online: Video,
  hybrid: MonitorPlay,
};

export function EventsPage({ navigate }: { navigate: (route: Route) => void }) {
  const [data, setData] = useState<EventListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [kind, setKind] = useState("all");
  const [format, setFormat] = useState("all");
  const [recommended, setRecommended] = useState(false);

  const load = () => {
    setLoading(true);
    setError(null);
    getEvents({
      kind: kind === "all" ? undefined : kind,
      format: format === "all" ? undefined : format,
      recommended: recommended || undefined,
      limit: 50,
    })
      .then(setData)
      .catch(() => setError("Не удалось загрузить события."))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [kind, format, recommended]);

  return (
    <div>
      <PageHeader
        eyebrow="События"
        title="События университетов"
        description="Дни открытых дверей, лекции, конкурсы и карьерные ярмарки. Все события привязаны к официальным источникам поддерживаемых университетов. Можно отфильтровать по рекомендованным вашим программам."
      />

      <Card className="mb-6">
        <CardContent className="flex flex-col gap-3 p-4 md:flex-row md:items-center">
          <div className="flex gap-2">
            <Select value={kind} onValueChange={setKind}>
              <SelectTrigger className="w-[200px]"><SelectValue placeholder="Тип" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Все типы</SelectItem>
                {KINDS.map((k) => <SelectItem key={k} value={k}>{eventKindLabel(k)}</SelectItem>)}
              </SelectContent>
            </Select>
            <Select value={format} onValueChange={setFormat}>
              <SelectTrigger className="w-[160px]"><SelectValue placeholder="Формат" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Все форматы</SelectItem>
                {FORMATS.map((f) => <SelectItem key={f} value={f}>{eventFormatLabel(f)}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2 md:ml-auto">
            <Switch id="rec" checked={recommended} onCheckedChange={setRecommended} />
            <Label htmlFor="rec" className="flex items-center gap-1 text-sm">
              <Sparkles className="h-3.5 w-3.5 text-primary" /> Только по моим программам
            </Label>
          </div>
        </CardContent>
      </Card>

      {loading && <Loading label="Загружаем события…" />}
      {error && <ErrorState message={error} onRetry={load} />}
      {data && !loading && !error && (
        data.items.length === 0 ? (
          <EmptyState title="События не найдены" message="Измените фильтры или сбросьте ограничение по рекомендациям." />
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {data.items.map((ev) => (
              <EventCard key={ev.id} event={ev} navigate={navigate} />
            ))}
          </div>
        )
      )}
    </div>
  );
}

export function EventCard({ event, navigate }: { event: EventItem; navigate: (route: Route) => void }) {
  const FormatIcon = FORMAT_ICON[event.format] ?? CalendarDays;
  return (
    <Card className="group flex flex-col transition hover:-translate-y-0.5 hover:shadow-md">
      <CardContent className="flex flex-1 flex-col gap-3 p-5">
        <div className="flex items-center justify-between gap-2">
          <div className="flex flex-wrap gap-1.5">
            <Tag tone="primary">{eventKindLabel(event.kind)}</Tag>
            <Tag tone="muted"><FormatIcon className="mr-1 inline h-3 w-3" />{eventFormatLabel(event.format)}</Tag>
          </div>
          <span className="text-xs text-muted-foreground">{relativeTime(event.startsAt)}</span>
        </div>
        <button onClick={() => navigate({ view: "event", id: event.id })} className="text-left">
          <h3 className="font-serif text-lg font-semibold leading-snug text-foreground group-hover:text-primary">
            {event.title}
          </h3>
        </button>
        {event.description && <p className="line-clamp-2 text-sm text-muted-foreground">{event.description}</p>}
        {event.programIds.length > 0 && (
          <div className="rounded-lg border border-border/60 bg-background/50 p-3">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Связанная программа</p>
            <button type="button" onClick={() => navigate({ view: "program", id: event.programIds[0] })} className="mt-1 text-left text-sm font-medium text-primary hover:underline">
              {event.programIds[0]}
            </button>
            <ProgramShortlistActions programId={event.programIds[0]} compact />
          </div>
        )}
        {event.programIds.length === 0 && (
          <p data-testid="event-source-gap" className="text-xs text-muted-foreground">
            Связь с образовательной программой не указана в официальном источнике.
          </p>
        )}
        <div className="mt-auto flex items-center justify-between gap-2 border-t border-border/60 pt-3 text-sm">
          <span className="text-muted-foreground">
            {formatDateTime(event.startsAt)}
          </span>
          <Button size="sm" variant="ghost" className="gap-1 text-primary group-hover:bg-primary group-hover:text-primary-foreground" onClick={() => navigate({ view: "event", id: event.id })}>
            Подробнее <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
