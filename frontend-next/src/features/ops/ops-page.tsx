"use client";

import { useEffect, useState } from "react";
import { Wrench, RefreshCw, ChevronRight, Loader2, Lock, Activity, CheckCircle2, XCircle, Clock } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PageHeader, Loading, ErrorState, Stat, SectionTitle, Tag } from "@/components/shared";
import { getIngestionRunsApi, getIngestionRunApi, retryIngestionApi } from "@/lib/api";
import { INGESTION_STATUS_LABELS } from "@/lib/labels";
import { formatDateTime } from "@/lib/format";
import type { IngestionRunSummary, IngestionRunDetail } from "@/lib/types";

const STATUS_ICON: Record<string, React.ComponentType<{ className?: string }>> = {
  running: Clock,
  completed: CheckCircle2,
  failed: XCircle,
};
const STATUS_TONE: Record<string, string> = {
  running: "text-amber-600",
  completed: "text-emerald-600",
  failed: "text-destructive",
};

export function OpsPage() {
  const [opsKey, setOpsKey] = useState("");
  const [authed, setAuthed] = useState(false);
  const [runs, setRuns] = useState<IngestionRunSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("all");
  const [detail, setDetail] = useState<IngestionRunDetail | null>(null);
  const [retrying, setRetrying] = useState(false);

  const loadRuns = async (key: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await getIngestionRunsApi({ status: status === "all" ? undefined : (status as never) }, key);
      setRuns(res.items);
    } catch {
      setError("Ops API недоступен или неверный ключ (возвращает 404 для защиты поверхности).");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authed) void loadRuns(opsKey || "demo-key");
  }, [status, authed]);

  const openDetail = async (id: string) => {
    try {
      const res = await getIngestionRunApi(id, opsKey || "demo-key");
      setDetail(res.run);
    } catch {
      setError("Не удалось загрузить детали run.");
    }
  };

  const retry = async () => {
    setRetrying(true);
    try {
      const res = await retryIngestionApi({ source: "bmstu_fixture" }, opsKey || "demo-key");
      setDetail(res.run);
      await loadRuns(opsKey || "demo-key");
    } finally {
      setRetrying(false);
    }
  };

  if (!authed) {
    return (
      <div>
        <PageHeader eyebrow="Ops" title="Операторская консоль" description="Доступ к ingestion API. Ключ хранится только в памяти страницы и передаётся заголовком X-Andromeda-Ops-Key." />
        <Card className="max-w-md">
          <CardContent className="space-y-4 p-6">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Lock className="h-5 w-5" />
              <p className="text-sm">Введите ops-ключ. При неверном ключе backend вернёт 404, чтобы не раскрывать наличие поверхности.</p>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="opskey">Ops key</Label>
              <Input id="opskey" type="password" value={opsKey} onChange={(e) => setOpsKey(e.target.value)} placeholder="ANDROMEDA_OPS_API_KEY" />
            </div>
            <Button className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90" onClick={() => { setAuthed(true); }}>
              <Wrench className="h-4 w-4" /> Войти
            </Button>
            <p className="text-xs text-muted-foreground">Подсказка: в demo-режиме подойдёт любой непустой ключ.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        eyebrow="Ops"
        title="Ingestion runs"
        description="Контроль ingestion: список запусков, детали и ограниченный retry. Без выдачи raw snapshots и credentials."
        actions={
          <Button variant="outline" size="sm" className="gap-1" onClick={retry} disabled={retrying}>
            {retrying ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Retry fixture
          </Button>
        }
      />

      <Card className="mb-6">
        <CardContent className="flex items-center gap-3 p-4">
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="w-[180px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Все статусы</SelectItem>
              <SelectItem value="running">Выполняется</SelectItem>
              <SelectItem value="completed">Завершён</SelectItem>
              <SelectItem value="failed">Ошибка</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={() => loadRuns(opsKey || "demo-key")} className="gap-1">
            <RefreshCw className="h-4 w-4" /> Обновить
          </Button>
          <Tag tone="muted" >ключ: {opsKey ? "•".repeat(6) : "demo"}</Tag>
        </CardContent>
      </Card>

      {loading && <Loading label="Загружаем runs…" />}
      {error && <ErrorState message={error} />}
      {!loading && !error && (
        <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <Card>
            <CardContent className="p-0">
              <div className="overflow-hidden rounded-xl border border-border/70">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-muted/50">
                      <TableHead>Run</TableHead>
                      <TableHead>Источник</TableHead>
                      <TableHead>Статус</TableHead>
                      <TableHead className="hidden md:table-cell">Начат</TableHead>
                      <TableHead className="w-10"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {runs.map((r) => {
                      const Icon = STATUS_ICON[r.status];
                      return (
                        <TableRow key={r.id} className="cursor-pointer" onClick={() => openDetail(r.id)}>
                          <TableCell className="font-mono text-xs">{r.id.slice(0, 18)}…</TableCell>
                          <TableCell>{r.source}</TableCell>
                          <TableCell>
                            <span className={`inline-flex items-center gap-1 text-sm font-medium ${STATUS_TONE[r.status]}`}>
                              <Icon className="h-4 w-4" /> {INGESTION_STATUS_LABELS[r.status]}
                            </span>
                          </TableCell>
                          <TableCell className="hidden text-muted-foreground md:table-cell">{formatDateTime(r.startedAt)}</TableCell>
                          <TableCell><ChevronRight className="h-4 w-4 text-muted-foreground" /></TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <SectionTitle>{detail ? "Детали run" : "Выберите run"}</SectionTitle>
            </CardHeader>
            <CardContent>
              {detail ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Activity className={`h-5 w-5 ${STATUS_TONE[detail.status]}`} />
                    <span className="font-mono text-xs">{detail.id}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <Stat label="Программ" value={detail.programCount} />
                    <Stat label="Дисциплин" value={detail.curriculumItemCount} />
                    <Stat label="Событий" value={detail.eventCount} />
                    <Stat label="Точек кампуса" value={detail.campusPointCount} />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <Stat label="Добавлено" value={detail.insertedCount} />
                    <Stat label="Обновлено" value={detail.updatedCount} />
                    <Stat label="Без изменений" value={detail.unchangedCount} />
                    <Stat label="Удалено" value={detail.removedCount} />
                  </div>
                  {detail.errorMessage && (
                    <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
                      {detail.errorMessage}
                    </div>
                  )}
                  <div className="flex flex-wrap gap-1.5">
                    {detail.sourceKinds.map((k) => <Tag key={k} tone="muted">{k}</Tag>)}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Нажмите на строку в таблице, чтобы увидеть детали.</p>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
