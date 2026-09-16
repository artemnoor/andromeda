"use client";

import { useEffect, useState } from "react";
import { ArrowLeft, Download, Layers, GraduationCap, Calculator, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PageHeader, Loading, ErrorState, Stat, ProvenanceChip, Tag, SectionTitle } from "@/components/shared";
import { getProgram, getCurriculum, getProgramAdmissions, calculateAdmissionFit } from "@/lib/api";
import {
  directionLabel,
  studyFormLabel,
  fundingLabel,
  competitionLabel,
  taxonomyLabel,
} from "@/lib/labels";
import { formatDecimal, formatInt, formatMoney, formatDate } from "@/lib/format";
import type {
  ProgramResponse,
  CurriculumResponse,
  ProgramAdmissionsResponse,
  AdmissionFitResponse,
  AdmissionOffering,
} from "@/lib/types";
import type { Route } from "@/lib/router";
import { ADMISSION_FIT_LABELS } from "@/lib/labels";

export function ProgramPage({ id, navigate }: { id: string; navigate: (route: Route) => void }) {
  const [program, setProgram] = useState<ProgramResponse | null>(null);
  const [curriculum, setCurriculum] = useState<CurriculumResponse | null>(null);
  const [admissions, setAdmissions] = useState<ProgramAdmissionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    Promise.all([getProgram(id), getCurriculum(id), getProgramAdmissions(id)])
      .then(([p, c, a]) => {
        if (!active) return;
        setProgram(p);
        setCurriculum(c);
        setAdmissions(a);
      })
      .catch(() => active && setError("Не удалось загрузить программу. Проверьте ID и доступность API."))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [id]);

  if (loading) return <Loading label="Загружаем программу, учебный план и поступление…" />;
  if (error || !program || !curriculum || !admissions)
    return <ErrorState title="Программа недоступна" message={error ?? undefined} />;

  const p = program.program;
  return (
    <div data-testid="program-page">
      <button
        onClick={() => navigate({ view: "catalog" })}
        className="mb-4 inline-flex items-center gap-1 text-sm font-medium text-muted-foreground transition hover:text-primary"
      >
        <ArrowLeft className="h-4 w-4" /> Назад в каталог
      </button>

      <PageHeader
        eyebrow={`${p.code} · ${directionLabel(p.directionId)}`}
        title={p.name}
        description={`Учебный год ${p.educationYear}. Направление ${p.directionId} — ${directionLabel(p.directionId)}. Данные получены из открытых источников МГТУ.`}
        actions={
          <>
            {p.studyPlanUrl && (
              <Button variant="outline" size="sm" className="gap-1" asChild>
                <a href={p.studyPlanUrl} target="_blank" rel="noopener noreferrer">
                  <Download className="h-4 w-4" /> План (PDF)
                </a>
              </Button>
            )}
            <Button
              size="sm"
              className="gap-1 bg-primary text-primary-foreground hover:bg-primary/90"
              onClick={() => navigate({ view: "compare" })}
            >
              <Layers className="h-4 w-4" /> Сравнить
            </Button>
          </>
        }
      />

      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Дисциплин" value={formatInt(curriculum.items.length)} />
        <Stat
          label="Часов всего"
          value={formatInt(curriculum.items.reduce((s, i) => s + i.hours, 0))}
        />
        <Stat
          label="ЗЕТ всего"
          value={formatDecimal(curriculum.items.reduce((s, i) => s + Number(i.credits ?? 0), 0), 1)}
        />
        <Stat label="Семестров" value={formatInt(new Set(curriculum.items.map((i) => i.semester).filter(Boolean)).size)} />
      </div>

      <Tabs defaultValue="curriculum">
        <TabsList className="mb-4">
          <TabsTrigger value="curriculum">Учебный план</TabsTrigger>
          <TabsTrigger value="admissions">Поступление</TabsTrigger>
          <TabsTrigger value="admission-fit">Шансы поступления</TabsTrigger>
        </TabsList>

        <TabsContent value="curriculum">
          <CurriculumTab curriculum={curriculum} />
        </TabsContent>
        <TabsContent value="admissions">
          <AdmissionsTab admissions={admissions} />
        </TabsContent>
        <TabsContent value="admission-fit">
          <AdmissionFitTab offerings={admissions.offerings} programId={p.id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function CurriculumTab({ curriculum }: { curriculum: CurriculumResponse }) {
  return (
    <Card data-testid="curriculum-table">
      <CardHeader className="flex flex-row items-center justify-between gap-3 pb-3">
        <div>
          <h2 className="font-serif text-xl font-semibold">Учебный план {curriculum.educationYear}</h2>
          <p className="text-sm text-muted-foreground">
            План снят {formatDate(curriculum.capturedAt)} · {curriculum.items.length} дисциплин
          </p>
        </div>
        {curriculum.sourceUrl && (
          <Button variant="ghost" size="sm" asChild>
            <a href={curriculum.sourceUrl} target="_blank" rel="noopener noreferrer">
              <Download className="h-4 w-4" /> План
            </a>
          </Button>
        )}
      </CardHeader>
      <CardContent>
        <div className="overflow-hidden rounded-xl border border-border/70">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead>Дисциплина</TableHead>
                <TableHead className="w-20">Сем.</TableHead>
                <TableHead className="w-24">Часы</TableHead>
                <TableHead className="w-20">ЗЕТ</TableHead>
                <TableHead className="hidden w-40 md:table-cell">Область</TableHead>
                <TableHead className="hidden w-32 md:table-cell">Форма</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {curriculum.items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium text-foreground">{item.discipline.name}</TableCell>
                  <TableCell className="tabular-nums text-muted-foreground">{item.semester ?? "—"}</TableCell>
                  <TableCell className="tabular-nums">{formatInt(item.hours)}</TableCell>
                  <TableCell className="tabular-nums text-muted-foreground">{formatDecimal(item.credits, 1)}</TableCell>
                  <TableCell className="hidden md:table-cell">
                    <Tag tone="muted">{taxonomyLabel(item.discipline.primaryArea)}</Tag>
                  </TableCell>
                  <TableCell className="hidden text-xs text-muted-foreground md:table-cell">
                    {item.assessmentTypes?.join(", ") ?? "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

function AdmissionsTab({ admissions }: { admissions: ProgramAdmissionsResponse }) {
  return (
    <div className="space-y-4" data-testid="admissions-section">
      {admissions.offerings.map((o) => (
        <Card key={o.id}>
          <CardHeader className="pb-3">
            <div className="flex flex-wrap items-center gap-2">
              <Tag tone="primary">{o.admissionYear}</Tag>
              <Tag>{studyFormLabel(o.studyForm)}</Tag>
              <Tag>{fundingLabel(o.fundingType)}</Tag>
              <Tag tone="muted">{o.scope === "program" ? "Программа" : "Направление"}</Tag>
              {o.places != null && <Tag tone="muted">{formatInt(o.places)} мест</Tag>}
            </div>
          </CardHeader>
          <CardContent className="grid gap-5 md:grid-cols-2">
            <div>
              <SectionTitle>Вступительные испытания</SectionTitle>
              <div className="space-y-2">
                {o.exams.map((e, i) => (
                  <div key={i} className="flex items-center justify-between rounded-lg border border-border/60 bg-card px-3 py-2 text-sm">
                    <span className="font-medium">{e.subject}</span>
                    <span className="flex items-center gap-2 text-muted-foreground">
                      {e.isChoice && <Tag tone="muted">на выбор</Tag>}
                      <span className="tabular-nums">мин. {e.minimumScore ?? "—"}</span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <div className="space-y-4">
              {o.passingScores.length > 0 && (
                <div>
                  <SectionTitle>Проходные баллы</SectionTitle>
                  <div className="space-y-2">
                    {o.passingScores.map((ps, i) => (
                      <div key={i} className="flex items-center justify-between rounded-lg border border-border/60 bg-card px-3 py-2 text-sm">
                        <span>{competitionLabel(ps.competitionType)}</span>
                        <span className="tabular-nums font-semibold">
                          {ps.status === "bvi" ? "БВИ" : formatDecimal(ps.score, 0)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {o.quotas.length > 0 && (
                <div>
                  <SectionTitle>Квоты</SectionTitle>
                  <div className="flex flex-wrap gap-2">
                    {o.quotas.map((q, i) => (
                      <Tag key={i} tone="muted">
                        {competitionLabel(q.quotaType)}: {q.places ?? "—"}
                      </Tag>
                    ))}
                  </div>
                </div>
              )}
              {o.tuition.length > 0 && (
                <div>
                  <SectionTitle>Стоимость обучения</SectionTitle>
                  {o.tuition.map((t, i) => (
                    <div key={i} className="flex items-center justify-between rounded-lg border border-border/60 bg-card px-3 py-2 text-sm">
                      <span className="text-muted-foreground">{t.academicYear} · {studyFormLabel(t.studyForm)}</span>
                      <span className="font-semibold tabular-nums">{formatMoney(t.amount, t.currency)}/год</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
      <ProvenanceChip prov={admissions.offerings[0]?.provenance[0]} />
    </div>
  );
}

function AdmissionFitTab({ offerings, programId }: { offerings: AdmissionOffering[]; programId: string }) {
  const budgetOfferings = offerings.filter((o) => o.fundingType === "budget");
  const [offeringId, setOffereringId] = useState(budgetOfferings[0]?.id ?? offerings[0]?.id ?? "");
  const [scores, setScores] = useState<{ subject: string; value: string }[]>([
    { subject: "Математика", value: "85" },
    { subject: "Русский язык", value: "82" },
    { subject: "Информатика и ИКТ", value: "88" },
  ]);
  const [result, setResult] = useState<AdmissionFitResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const compute = async () => {
    setLoading(true);
    try {
      const res = await calculateAdmissionFit(programId, {
        version: 1,
        offeringId,
        applicant: {
          version: 1,
          scores: scores
            .filter((s) => s.subject && s.value)
            .map((s) => ({ subject: s.subject, score: Number(s.value) })),
        },
      });
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  const toneCls = result
    ? ADMISSION_FIT_LABELS[result.status].tone === "good"
      ? "text-emerald-700 bg-emerald-50 border-emerald-200"
      : ADMISSION_FIT_LABELS[result.status].tone === "warn"
        ? "text-amber-700 bg-amber-50 border-amber-200"
        : ADMISSION_FIT_LABELS[result.status].tone === "bad"
          ? "text-orange-700 bg-orange-50 border-orange-200"
          : "text-stone-600 bg-stone-50 border-stone-200"
    : "";

  return (
    <Card>
      <CardHeader className="pb-3">
        <h2 className="flex items-center gap-2 font-serif text-xl font-semibold">
          <Calculator className="h-5 w-5 text-primary" /> Калькулятор шансов поступления
        </h2>
        <p className="text-sm text-muted-foreground">
          Отдельное измерение от Content Fit: оценка реалистичности по вашим баллам ЕГЭ и проходным ориентирам прошлого года.
        </p>
      </CardHeader>
      <CardContent className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>Вариант набора</Label>
            <Select value={offeringId} onValueChange={setOffereringId}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {budgetOfferings.map((o) => (
                  <SelectItem key={o.id} value={o.id}>
                    {o.admissionYear} · {studyFormLabel(o.studyForm)} · {fundingLabel(o.fundingType)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Баллы ЕГЭ</Label>
            {scores.map((s, i) => (
              <div key={i} className="flex gap-2">
                <Input
                  value={s.subject}
                  onChange={(e) => setScores((prev) => prev.map((x, j) => (j === i ? { ...x, subject: e.target.value } : x)))}
                  placeholder="Предмет"
                />
                <Input
                  type="number"
                  min={0}
                  max={100}
                  value={s.value}
                  onChange={(e) => setScores((prev) => prev.map((x, j) => (j === i ? { ...x, value: e.target.value } : x)))}
                  className="w-24"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setScores((prev) => prev.filter((_, j) => j !== i))}
                  className="text-muted-foreground"
                >
                  ✕
                </Button>
              </div>
            ))}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setScores((prev) => [...prev, { subject: "", value: "" }])}
            >
              + Добавить предмет
            </Button>
          </div>
          <Button onClick={compute} disabled={loading} className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
            {loading ? "Считаем…" : "Рассчитать"} <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        <div>
          {result ? (
            <div className="space-y-4">
              <div className={`rounded-xl border p-4 ${toneCls}`}>
                <p className="text-sm font-medium">Итог</p>
                <p className="font-serif text-3xl font-bold tabular-nums">{ADMISSION_FIT_LABELS[result.status].label}</p>
                <p className="text-sm opacity-80">Оценка готовности: {result.score}/100 · ваш балл {result.applicantTotalScore}</p>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <Stat label="Мин. готовность" value={result.breakdown.minimumReadiness} />
                <Stat label="Проходная готовность" value={result.breakdown.passingReadiness} />
                <Stat label="Полнота данных" value={result.breakdown.dataCompleteness} />
              </div>
              {result.reasons.length > 0 && (
                <div>
                  <SectionTitle>Почему так</SectionTitle>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    {result.reasons.map((r, i) => <li key={i}>• {r}</li>)}
                  </ul>
                </div>
              )}
              {result.dataGaps.length > 0 && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                  {result.dataGaps.join(" ")}
                </div>
              )}
            </div>
          ) : (
            <div className="flex h-full flex-col items-center justify-center rounded-xl border border-dashed border-border/70 p-8 text-center text-sm text-muted-foreground">
              <GraduationCap className="mb-2 h-8 w-8 text-primary/50" />
              Выберите вариант набора, введите баллы ЕГЭ и нажмите «Рассчитать».
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
