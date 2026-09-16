"use client";

import { useMemo, useState } from "react";
import { Search, ArrowRight, BookOpen, GraduationCap } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PageHeader, Tag, Loading, ErrorState } from "@/components/shared";
import { directionLabel } from "@/lib/labels";
import type { ProgramSummary } from "@/lib/types";
import type { Route } from "@/lib/router";

export function CatalogPage({
  programs,
  loading,
  error,
  navigate,
}: {
  programs: ProgramSummary[];
  loading: boolean;
  error: string | null;
  navigate: (route: Route) => void;
}) {
  const [query, setQuery] = useState("");
  const [direction, setDirection] = useState("all");
  const [year, setYear] = useState("all");

  const directions = useMemo(() => [...new Set(programs.map((p) => p.directionId))].sort(), [programs]);
  const years = useMemo(() => [...new Set(programs.map((p) => p.educationYear))].sort().reverse(), [programs]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return programs.filter((p) => {
      if (direction !== "all" && p.directionId !== direction) return false;
      if (year !== "all" && p.educationYear !== year) return false;
      if (!q) return true;
      return (
        p.name.toLowerCase().includes(q) ||
        p.code.toLowerCase().includes(q) ||
        p.directionId.toLowerCase().includes(q) ||
        directionLabel(p.directionId).toLowerCase().includes(q)
      );
    });
  }, [programs, query, direction, year]);

  if (loading) return <Loading label="Загружаем каталог программ…" />;
  if (error) return <ErrorState title="Каталог недоступен" message={error} />;

  return (
    <div>
      <PageHeader
        eyebrow="Каталог"
        title="Образовательные программы МГТУ"
        description="Полный каталог программ бакалавриата с привязкой к учебным планам, поступлению и сравнению. Источник — открытые данные приёмной комиссии."
      />

      <Card className="mb-6 border-border/70 bg-card/80">
        <CardContent className="flex flex-col gap-3 p-4 md:flex-row md:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Поиск по коду, названию или направлению…"
              className="pl-9"
            />
          </div>
          <div className="flex gap-2">
            <Select value={direction} onValueChange={setDirection}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Направление" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Все направления</SelectItem>
                {directions.map((d) => (
                  <SelectItem key={d} value={d}>
                    {d} · {directionLabel(d)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={year} onValueChange={setYear}>
              <SelectTrigger className="w-[130px]">
                <SelectValue placeholder="Год" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Все годы</SelectItem>
                {years.map((y) => (
                  <SelectItem key={y} value={y}>{y}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <p className="mb-4 text-sm text-muted-foreground">
        Найдено программ: <span className="font-semibold text-foreground">{filtered.length}</span>
      </p>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((p) => (
          <Card
            key={p.id}
            className="group flex flex-col border-border/70 transition hover:-translate-y-0.5 hover:shadow-md"
          >
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 rounded-md bg-primary/10 px-2 py-0.5 font-mono text-xs font-semibold text-primary">
                  <GraduationCap className="h-3.5 w-3.5" />
                  {p.code}
                </span>
                <Tag tone="muted">{p.educationYear}</Tag>
              </div>
              <h3 className="mt-2 font-serif text-lg font-semibold leading-snug text-foreground">
                {p.name}
              </h3>
            </CardHeader>
            <CardContent className="flex-1 pb-3">
              <p className="text-sm text-muted-foreground">
                Направление <span className="font-medium text-foreground">{directionLabel(p.directionId)}</span>
              </p>
            </CardContent>
            <CardFooter className="flex items-center justify-between gap-2 border-t border-border/60 pt-3">
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                <BookOpen className="h-3.5 w-3.5" /> учебный план · поступление
              </span>
              <Button
                size="sm"
                variant="ghost"
                className="gap-1 text-primary group-hover:bg-primary group-hover:text-primary-foreground"
                onClick={() => navigate({ view: "program", id: p.id })}
              >
                Открыть <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>

      {filtered.length === 0 && (
        <Card className="border-dashed">
          <CardContent className="p-10 text-center text-sm text-muted-foreground">
            Ничего не нашлось. Попробуйте изменить запрос или сбросить фильтры.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
