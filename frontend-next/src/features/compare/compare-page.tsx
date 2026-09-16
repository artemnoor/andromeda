"use client";

import { useEffect, useState } from "react";
import { ArrowLeftRight, GitCompare, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PageHeader, Loading, ErrorState, Stat, SectionTitle, Tag } from "@/components/shared";
import { comparePrograms, getPrograms } from "@/lib/api";
import { directionLabel } from "@/lib/labels";
import { formatDecimal, formatInt, formatShare } from "@/lib/format";
import type { AreaBreakdownItem, ComparisonResponse, ProgramSummary } from "@/lib/types";
import type { Route } from "@/lib/router";

export function ComparePage({
  programs,
  navigate,
}: {
  programs: ProgramSummary[];
  navigate: (route: Route) => void;
}) {
  const [aId, setAId] = useState(programs[0]?.id ?? "");
  const [bId, setBId] = useState(programs[1]?.id ?? "");
  const [scope, setScope] = useState<"all" | "semester">("all");
  const [semester, setSemester] = useState(3);
  const [data, setData] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (programs.length && !aId) setAId(programs[0].id);
    if (programs.length > 1 && !bId) setBId(programs[1].id);
  }, [programs, aId, bId]);

  const run = async (a: string, b: string, sc: "all" | "semester", sem: number) => {
    if (!a || !b || a === b) return;
    setLoading(true);
    setError(null);
    try {
      const res = await comparePrograms([a, b], { scope: sc, semester: sc === "semester" ? sem : undefined });
      setData(res);
    } catch {
      setError("Не удалось загрузить сравнение.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void run(aId, bId, scope, semester);
  }, [aId, bId, scope, semester]);

  return (
    <div>
      <PageHeader
        eyebrow="Сравнение"
        title="Сравнение программ"
        description="Выберите две программы и сопоставьте учебные планы: дисциплины, нагрузку в часах и кредитах. Переключайтесь между полным планом и отдельным семестром."
      />

      <Card className="mb-6">
        <CardContent className="flex flex-col gap-4 p-4 lg:flex-row lg:items-end">
          <div className="grid flex-1 gap-3 sm:grid-cols-2 lg:grid-cols-[1fr_auto_1fr]">
            <ProgramSelect label="Программа A" value={aId} onChange={setAId} programs={programs} exclude={bId} />
            <div className="hidden items-center justify-center lg:flex">
              <ArrowLeftRight className="h-5 w-5 text-muted-foreground" />
            </div>
            <ProgramSelect label="Программа B" value={bId} onChange={setBId} programs={programs} exclude={aId} />
          </div>
          <div className="flex items-end gap-3">
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">Режим</p>
              <Tabs value={scope} onValueChange={(v) => setScope(v as "all" | "semester")}>
                <TabsList>
                  <TabsTrigger value="all">Весь план</TabsTrigger>
                  <TabsTrigger value="semester">Семестр</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
            {scope === "semester" && (
              <div>
                <p className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">Семестр</p>
                <Select value={String(semester)} onValueChange={(v) => setSemester(Number(v))}>
                  <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                      <SelectItem key={s} value={String(s)}>{s}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {loading && <Loading label="Сравниваем учебные планы…" />}
      {error && <ErrorState message={error} />}
      {data && !loading && !error && <CompareResult data={data} navigate={navigate} />}
    </div>
  );
}

function ProgramSelect({
  label,
  value,
  onChange,
  programs,
  exclude,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  programs: ProgramSummary[];
  exclude: string;
}) {
  return (
    <div>
      <p className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger><SelectValue /></SelectTrigger>
        <SelectContent>
          {programs.filter((p) => p.id !== exclude).map((p) => (
            <SelectItem key={p.id} value={p.id}>
              {p.code} · {p.name.split("·")[0].trim()}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

function CompareResult({ data, navigate }: { data: ComparisonResponse; navigate: (route: Route) => void }) {
  const a = data.programA;
  const b = data.programB;
  return (
    <div className="space-y-6">
      <div className="grid gap-3 md:grid-cols-2">
        <ProgramHeader program={a} tone="A" navigate={navigate} />
        <ProgramHeader program={b} tone="B" navigate={navigate} />
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Часы A" value={formatInt(data.totalsA.totalHours)} />
        <Stat label="Часы B" value={formatInt(data.totalsB.totalHours)} />
        <Stat label="ЗЕТ A" value={formatDecimal(data.totalsA.totalCredits, 1)} />
        <Stat label="ЗЕТ B" value={formatDecimal(data.totalsB.totalCredits, 1)} />
      </div>

      <AreaComparisonChart data={data} />

      <Card>
        <CardHeader className="pb-3">
          <SectionTitle hint={`${data.rows.length} строк`}>Дисциплины</SectionTitle>
        </CardHeader>
        <CardContent>
          <div className="max-h-[28rem] overflow-y-auto warm-scroll rounded-xl border border-border/70">
            <Table>
              <TableHeader className="sticky top-0">
                <TableRow className="bg-muted/70">
                  <TableHead>Дисциплина</TableHead>
                  <TableHead className="w-16">Сем.</TableHead>
                  <TableHead className="text-right">Часы A</TableHead>
                  <TableHead className="text-right">Часы B</TableHead>
                  <TableHead className="text-right">Δ</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.rows.map((row, i) => (
                  <TableRow key={i}>
                    <TableCell className="font-medium">
                      {row.discipline}
                      {!row.presentA && <Tag tone="muted">только B</Tag>}
                      {!row.presentB && <Tag tone="muted">только A</Tag>}
                    </TableCell>
                    <TableCell className="tabular-nums text-muted-foreground">{row.semester ?? "—"}</TableCell>
                    <TableCell className="text-right tabular-nums">{row.hoursA ?? "—"}</TableCell>
                    <TableCell className="text-right tabular-nums">{row.hoursB ?? "—"}</TableCell>
                    <TableCell className={`text-right tabular-nums ${(row.deltaHours ?? 0) > 0 ? "text-emerald-600" : (row.deltaHours ?? 0) < 0 ? "text-orange-600" : "text-muted-foreground"}`}>
                      {row.deltaHours == null ? "—" : `${row.deltaHours > 0 ? "+" : ""}${row.deltaHours}`}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

type AreaComparisonRow = {
  code: string;
  name: string;
  shareA: number;
  shareB: number;
};

function areaShare(value: string | number | null | undefined): number {
  const parsed = typeof value === "number" ? value : Number(value ?? 0);
  return Number.isFinite(parsed) ? Math.max(0, Math.min(1, parsed)) : 0;
}

function mergeAreaBreakdowns(
  areaBreakdownA: AreaBreakdownItem[] | null | undefined,
  areaBreakdownB: AreaBreakdownItem[] | null | undefined,
): AreaComparisonRow[] {
  const merged = new Map<string, AreaComparisonRow>();

  for (const item of areaBreakdownA ?? []) {
    const current = merged.get(item.code) ?? { code: item.code, name: item.name, shareA: 0, shareB: 0 };
    merged.set(item.code, { ...current, name: current.name || item.name, shareA: areaShare(item.share) });
  }
  for (const item of areaBreakdownB ?? []) {
    const current = merged.get(item.code) ?? { code: item.code, name: item.name, shareA: 0, shareB: 0 };
    merged.set(item.code, { ...current, name: current.name || item.name, shareB: areaShare(item.share) });
  }

  return [...merged.values()].sort((left, right) => {
    const totalDelta = right.shareA + right.shareB - left.shareA - left.shareB;
    return totalDelta || left.name.localeCompare(right.name, "ru");
  });
}

function AreaComparisonChart({ data }: { data: ComparisonResponse }) {
  const rows = mergeAreaBreakdowns(data.areaBreakdownA, data.areaBreakdownB);

  return (
    <Card data-testid="comparison-area-chart">
      <CardHeader className="pb-3">
        <SectionTitle hint={rows.length ? `${rows.length} категорий` : "нет данных"}>
          Содержание по категориям
        </SectionTitle>
        <p className="max-w-3xl text-sm text-muted-foreground">
          Доля учебной нагрузки, распределённая по 22 областям taxonomy. Каждая строка показывает одну и ту же категорию для обеих программ.
        </p>
        <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted-foreground" aria-label="Легенда диаграммы">
          <span className="inline-flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-primary" aria-hidden="true" />
            <span><strong className="text-foreground">A</strong> · {data.programA.code}</span>
          </span>
          <span className="inline-flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-secondary" aria-hidden="true" />
            <span><strong className="text-foreground">B</strong> · {data.programB.code}</span>
          </span>
        </div>
      </CardHeader>
      <CardContent>
        {rows.length === 0 ? (
          <p className="rounded-xl border border-dashed border-border/70 p-5 text-sm text-muted-foreground">
            Для выбранного среза нет распределения по категориям.
          </p>
        ) : (
          <div className="space-y-4" role="list" aria-label="Сравнение категорий дисциплин">
            {rows.map((row) => (
              <div
                key={row.code}
                role="listitem"
                className="grid gap-2 rounded-xl border border-border/60 bg-background/40 p-3 sm:grid-cols-[minmax(12rem,0.9fr)_minmax(14rem,2fr)] sm:items-center"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-foreground" title={row.name}>{row.name}</p>
                  <p className="mt-0.5 font-mono text-[10px] uppercase tracking-wide text-muted-foreground">{row.code}</p>
                </div>
                <div className="space-y-2">
                  <AreaBar label="A" name={row.name} value={row.shareA} tone="primary" />
                  <AreaBar label="B" name={row.name} value={row.shareB} tone="secondary" />
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function AreaBar({ label, name, value, tone }: { label: "A" | "B"; name: string; value: number; tone: "primary" | "secondary" }) {
  const percent = value * 100;
  return (
    <div className="flex items-center gap-2">
      <span className={`w-4 text-center text-[10px] font-bold ${tone === "primary" ? "text-primary" : "text-secondary"}`}>{label}</span>
      <div
        className="h-2.5 flex-1 overflow-hidden rounded-full bg-muted"
        role="progressbar"
        aria-label={`Программа ${label}, ${name}`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Number(percent.toFixed(2))}
        aria-valuetext={formatShare(value)}
      >
        <div
          className={`h-full rounded-full transition-[width] duration-500 ${tone === "primary" ? "bg-primary" : "bg-secondary"}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="w-12 text-right text-xs font-mono tabular-nums text-muted-foreground">{formatShare(value)}</span>
    </div>
  );
}

function ProgramHeader({ program, tone, navigate }: { program: ProgramSummary; tone: "A" | "B"; navigate: (route: Route) => void }) {
  return (
    <Card className="border-l-4 border-l-primary">
      <CardContent className="p-4">
        <div className="mb-1 flex items-center gap-2">
          <span className="grid h-6 w-6 place-items-center rounded-full bg-primary text-xs font-bold text-primary-foreground">{tone}</span>
          <span className="font-mono text-xs font-semibold text-primary">{program.code}</span>
        </div>
        <button onClick={() => navigate({ view: "program", id: program.id })} className="text-left font-serif text-lg font-semibold leading-snug hover:text-primary">
          {program.name}
        </button>
        <p className="mt-1 text-xs text-muted-foreground">{directionLabel(program.directionId)} · {program.educationYear}</p>
      </CardContent>
    </Card>
  );
}
