"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowRight, ArrowLeft, CheckCircle2, Sparkles, RotateCcw, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { PageHeader, Loading, ErrorState, Stat, SectionTitle, Tag, ScoreBadge } from "@/components/shared";
import { ApiError, completeProftestSession, getCurrentProftestSession, nextProftestSession, saveProftestSession, startProftestSession } from "@/lib/api";
import { taxonomyLabel } from "@/lib/labels";
import { formatPercent } from "@/lib/format";
import type { DecisionContextData, DecisionSuggestionsData, ProftestSessionAnswerRequest, ProftestSessionResponse, Question, ProftestResultsResponse } from "@/lib/types";
import type { Route } from "@/lib/router";
import { cn } from "@/lib/utils";
import { useDecisionContext } from "@/features/decision/decision-context";

const QUESTION_SET_VERSION = "proftest-v3";
const ANSWERS_STORAGE_KEY = `andromeda:proftest:${QUESTION_SET_VERSION}:session-answers`;

export function ProftestPage({ navigate }: { navigate: (route: Route) => void }) {
  const { context, suggestions, refresh, refreshSuggestions } = useDecisionContext();
  const [session, setSession] = useState<ProftestSessionResponse | null>(null);
  const [questionHistory, setQuestionHistory] = useState<Record<string, Question>>({});
  const [answers, setAnswers] = useState<Record<string, ProftestSessionAnswerRequest>>(() => readAnswers());
  const [shownQuestionId, setShownQuestionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [phase, setPhase] = useState<"intro" | "test" | "results">("intro");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    getCurrentProftestSession()
      .then((current) => {
        if (!active) return;
        acceptSession(current);
        if (current.status === "completed" && current.results) setPhase("results");
        else setPhase("test");
      })
      .catch((reason: unknown) => {
        if (!active) return;
        if (reason instanceof ApiError && reason.status === 404) setPhase("intro");
        else setError("Не удалось восстановить сессию профтеста.");
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    window.localStorage.setItem(ANSWERS_STORAGE_KEY, JSON.stringify(answers));
  }, [answers]);

  useEffect(() => {
    if (phase !== "results") return;
    // Completion persists only UserProfile. Hydrate the shared decision
    // projection and derived suggestions explicitly; no choice mutation is
    // performed by either read.
    void refresh().then(() => refreshSuggestions());
  }, [phase, refresh, refreshSuggestions]);

  const current = useMemo(() => {
    if (shownQuestionId) return questionHistory[shownQuestionId] ?? session?.currentQuestion ?? null;
    return session?.currentQuestion ?? null;
  }, [questionHistory, session, shownQuestionId]);

  function acceptSession(next: ProftestSessionResponse): void {
    setSession(next);
    setShownQuestionId(null);
    if (next.questionSetVersion !== QUESTION_SET_VERSION) {
      setAnswers({});
    }
    if (next.staleQuestionIds.length > 0) {
      const stale = new Set(next.staleQuestionIds);
      setAnswers((previous) => Object.fromEntries(Object.entries(previous).filter(([id]) => !stale.has(id))));
      setQuestionHistory((previous) => Object.fromEntries(Object.entries(previous).filter(([id]) => !stale.has(id))));
    }
    if (next.currentQuestion) setQuestionHistory((previous) => ({ ...previous, [next.currentQuestion!.id]: next.currentQuestion! }));
  }

  const start = async () => {
    setBusy(true); setError(null);
    try {
      const next = await startProftestSession();
      acceptSession(next); setPhase("test");
    } catch { setError("Не удалось начать профтест."); }
    finally { setBusy(false); }
  };

  const updateAnswer = (question: Question, patch: Partial<ProftestSessionAnswerRequest>) => {
    setAnswers((previous) => {
      const previousAnswer = previous[question.id];
      return {
        ...previous,
        [question.id]: {
          ...previousAnswer,
          ...patch,
          questionId: question.id,
          optionIds: patch.optionIds ?? previousAnswer?.optionIds ?? [],
          status: patch.status ?? previousAnswer?.status ?? "answered",
        },
      };
    });
  };

  const advance = async () => {
    if (!session || !current) return;
    const answer = answers[current.id] ?? { questionId: current.id, optionIds: [], status: "uncertain" as const };
    if (current.required && (answer.optionIds ?? []).length === 0 && answer.status === "answered") return;
    setBusy(true); setError(null);
    try {
      const next = session.currentQuestion?.id === current.id
        ? await nextProftestSession(answer, session.revision)
        : await saveProftestSession([answer], session.revision);
      acceptSession(next);
      if (next.currentQuestion) setPhase("test");
      else await complete();
    } catch (reason: unknown) {
      setError(reason instanceof ApiError && reason.status === 409 ? "Сессия изменилась в другой вкладке. Обновите страницу и продолжите с последнего сохранённого шага." : "Не удалось сохранить ответ.");
    } finally { setBusy(false); }
  };

  const complete = async () => {
    setBusy(true); setError(null);
    try {
      const completed = await completeProftestSession();
      acceptSession(completed);
      if (completed.results) setPhase("results");
      else setError("Профиль сохранён, но рекомендации пока недоступны.");
    } catch { setError("Не удалось собрать рекомендации."); }
    finally { setBusy(false); }
  };

  const goBack = () => {
    if (!current) return;
    const previous = Object.values(questionHistory).filter((item) => item.order < current.order).sort((a, b) => b.order - a.order)[0];
    if (previous) setShownQuestionId(previous.id);
  };

  if (loading) return <Loading label="Восстанавливаем сессию профтеста…" />;
  if (error && !current && phase !== "intro") return <ErrorState message={error} />;
  if (phase === "intro") return <Intro onStart={start} busy={busy} error={error} />;
  if (phase === "results" && session?.results) return <ResultsView results={session.results} profileRevision={session.profileRevision ?? context?.profileRevision ?? null} decisionContext={context} suggestions={suggestions} navigate={navigate} onRestart={() => { setSession(null); setAnswers({}); setQuestionHistory({}); setPhase("intro"); }} />;
  if (!session) return <Loading label="Готовим следующий шаг…" />;
  if (!current && session.preliminary) return <AdaptiveStopped session={session} onComplete={() => void complete()} busy={busy} />;
  if (!current) return <Loading label="Готовим следующий шаг…" />;

  return (
    <div className="mx-auto w-full max-w-3xl">
      <div data-testid="proftest-question" data-question-id={current.id}>
      <PageHeader eyebrow={`${current.stage ?? current.block} · ${current.componentType}`} title={current.prompt} description={current.helperText ?? componentHint(current.componentType)} />
      <div className="mb-6 flex items-center gap-3" aria-label="Прогресс профтеста">
        <Progress value={Math.max(5, ((session.progress.stageIndex + 1) / session.progress.stageCount) * 100)} className="h-2 flex-1" />
        <span className="text-xs tabular-nums text-muted-foreground">осталось {session.progress.minRemaining}–{session.progress.maxRemaining}</span>
      </div>
      </div>
      {session.preliminary && <PreliminaryBanner topics={session.preliminary.topics} adaptive={session.adaptive} />}
      <QuestionView question={current} answer={answers[current.id]} onChange={(optionIds) => updateAnswer(current, { optionIds, status: "answered" })} onIntensity={(intensity) => updateAnswer(current, { intensity })} onUncertain={() => updateAnswer(current, { optionIds: [], status: "uncertain" })} onSkip={() => updateAnswer(current, { optionIds: [], status: "skipped" })} />
      {error && <p role="alert" className="mt-4 rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">{error}</p>}
      <div className="mt-6 flex items-center justify-between gap-3">
        <Button variant="ghost" disabled={busy || current.order === 0 || Object.keys(questionHistory).length < 2} onClick={goBack} className="gap-1"><ArrowLeft className="h-4 w-4" /> Назад</Button>
        <Button data-testid="proftest-next" onClick={() => void advance()} disabled={busy || (current.required && (answers[current.id]?.optionIds ?? []).length === 0 && !["uncertain", "skipped"].includes(answers[current.id]?.status ?? "answered"))} className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
          {current.adaptive ? "Уточнить результат" : "Далее"}
        </Button>
      </div>
    </div>
  );
}

function Intro({ onStart, busy, error }: { onStart: () => void; busy: boolean; error: string | null }) {
  return <div data-testid="proftest-intro"><PageHeader eyebrow="Профтест" title="Профессиональный тест" description="За несколько минут определим, какие направления тебе ближе по реальному содержанию учебных программ. После короткого ядра тест задаст только полезные уточнения." /><Card><CardContent className="flex flex-col items-start gap-4 p-6 md:flex-row md:items-center md:justify-between"><div className="space-y-2"><div className="flex flex-wrap gap-2"><Tag tone="primary">≈10 вопросов</Tag><Tag tone="muted">3 минуты</Tag><Tag tone="muted">гостевой режим</Tag></div><p className="max-w-xl text-sm text-muted-foreground">Сначала будет 5 сильных вопросов, затем — до 4 адаптивных. Прогресс сохранится в текущей сессии; аккаунт не нужен.</p></div><Button data-testid="proftest-start" size="lg" disabled={busy} className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90" onClick={onStart}>{busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />} Начать тест</Button></CardContent></Card>{error && <p role="alert" className="mt-4 text-sm text-destructive">{error}</p>}</div>;
}

function PreliminaryBanner({ topics, adaptive }: { topics: { code: string; label: string }[]; adaptive: ProftestSessionResponse["adaptive"] }) {
  return <Card data-testid="proftest-preliminary" className="mb-6 border-primary/20 bg-primary/[0.03]"><CardContent className="space-y-3 p-4"><div><p className="font-medium">Мы уже видим твой профиль</p><p className="text-sm text-muted-foreground">Осталось уточнить несколько моментов — без лишних вопросов.</p></div><div className="flex flex-wrap gap-2" aria-label="Предварительные направления">{topics.map((topic) => <Tag key={topic.code} tone="primary">{topic.label}</Tag>)}</div>{adaptive?.status === "skipped" && <p className="text-xs text-muted-foreground">Профиль уже достаточно устойчив, можно переходить к результатам.</p>}</CardContent></Card>;
}

function AdaptiveStopped({ session, onComplete, busy }: { session: ProftestSessionResponse; onComplete: () => void; busy: boolean }) {
  const reason = session.adaptive?.stopReason === "insufficient_candidates" ? "Для уточнения сейчас недостаточно программ в каталоге." : session.adaptive?.stopReason === "source_gap" ? "В каталоге пока недостаточно данных для дополнительного уточнения." : "Профиль уже достаточно устойчив — дополнительных вопросов не требуется.";
  return <div data-testid="proftest-adaptive-stopped" className="mx-auto w-full max-w-3xl"><PageHeader eyebrow="Профиль готов" title="Можно посмотреть результат" description={reason} /><Card><CardContent className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between"><div className="flex flex-wrap gap-2">{session.preliminary?.topics.map((topic) => <Tag key={topic.code} tone="primary">{topic.label}</Tag>)}</div><Button data-testid="proftest-complete" disabled={busy} onClick={onComplete} className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90">{busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />} Показать результат</Button></CardContent></Card></div>;
}

function QuestionView({ question, answer, onChange, onIntensity, onUncertain, onSkip }: { question: Question; answer?: ProftestSessionAnswerRequest; onChange: (ids: string[]) => void; onIntensity: (value: number) => void; onUncertain: () => void; onSkip: () => void }) {
  const selected = answer?.optionIds ?? [];
  const toggle = (id: string) => question.multiSelect ? onChange(selected.includes(id) ? selected.filter((item) => item !== id) : selected.length < question.maxSelected ? [...selected, id] : selected) : onChange([id]);
  return <div data-component={question.componentType} className="space-y-4"><div className="grid gap-3 sm:grid-cols-2">{question.options.map((option) => { const active = selected.includes(option.id); return <button data-testid="proftest-option" key={option.id} type="button" aria-pressed={active} onClick={() => toggle(option.id)} className={cn("flex min-h-12 items-center gap-3 rounded-xl border p-4 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary", active ? "border-primary bg-primary/5 ring-1 ring-primary" : "border-border/70 bg-card hover:border-primary/40 hover:bg-accent/50")}><span className={cn("grid h-5 w-5 shrink-0 place-items-center rounded-md border", active ? "border-primary bg-primary text-primary-foreground" : "border-border")}>{active && <CheckCircle2 className="h-4 w-4" />}</span><span className="text-sm font-medium">{option.label}</span></button>; })}</div>{question.multiSelect && <p className="text-xs text-muted-foreground">Можно выбрать до {question.maxSelected} вариантов.</p>}{question.multiSelect && selected.length > 0 && <label className="block rounded-xl border bg-card p-4 text-sm"><span className="flex justify-between"><span>Насколько это выражено?</span><output>{Math.round(Number(answer?.intensity ?? 0.5) * 100)}%</output></span><input aria-label="Интенсивность" type="range" min="0" max="1" step="0.05" value={Number(answer?.intensity ?? 0.5)} onChange={(event) => onIntensity(Number(event.target.value))} className="mt-3 w-full" /></label>}{question.allowUncertain && <Button variant="outline" size="sm" onClick={onUncertain}>Не уверен</Button>}{question.allowSkip && <Button variant="outline" size="sm" onClick={onSkip}>Пропустить</Button>}</div>;
}

function ResultsView({ results, profileRevision, decisionContext, suggestions, navigate, onRestart }: { results: ProftestResultsResponse; profileRevision: number | null; decisionContext: DecisionContextData | null; suggestions: DecisionSuggestionsData | null; navigate: (route: Route) => void; onRestart: () => void }) {
  const prof = results.profile;
  const shortlistCount = decisionContext?.state.choice.shortlistEntries.filter((entry) => entry.state === "active").length ?? 0;
  return <div data-testid="proftest-results"><PageHeader eyebrow="Результаты профтеста" title="Ваш профиль готов" description={`Уверенность профиля — ${formatPercent(prof.confidence, 0)}. Ниже — программы с объяснением совпадений.`} actions={<Button variant="outline" size="sm" className="gap-1" onClick={onRestart}><RotateCcw className="h-4 w-4" /> Пройти заново</Button>} /><Card data-testid="proftest-decision-handoff" className="mb-6 border-primary/20 bg-primary/[0.03]"><CardContent className="flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between"><div className="space-y-1"><p className="font-serif text-lg font-semibold">Профиль уточнён</p><p className="text-sm text-muted-foreground">Профиль обновил предложения системы{profileRevision !== null ? ` · ревизия ${profileRevision}` : ""}. Сохранённые варианты не изменены автоматически.</p>{suggestions && <p className="text-xs text-muted-foreground">Сейчас доступны {suggestions.suggestions.length} системных предложений{suggestions.refinementQuestion ? " и один вопрос для уточнения различия" : ""}. Shortlist: {shortlistCount}.</p>}</div><div className="flex flex-wrap gap-2"><Button type="button" onClick={() => navigate({ view: "decision" })}>Открыть «Мой выбор»</Button>{shortlistCount >= 2 && <Button type="button" variant="outline" onClick={() => navigate({ view: "compare" })}>Сравнить shortlist</Button>}</div></CardContent></Card><div className="grid gap-6 lg:grid-cols-[1fr_1.4fr]"><Card><CardHeader className="pb-3"><SectionTitle>Ваши интересы</SectionTitle></CardHeader><CardContent className="space-y-4"><div className="space-y-2">{prof.preferredSubjectWeights.map((weight) => <div key={weight.code}><div className="flex justify-between text-sm"><span>{taxonomyLabel(weight.code)}</span><span className="tabular-nums text-muted-foreground">{formatPercent(weight.weight, 0)}</span></div><Progress value={Number(weight.weight) * 100} className="h-1.5" /></div>)}</div><div className="grid grid-cols-2 gap-3"><Stat label="Уверенность" value={formatPercent(prof.confidence, 0)} /><Stat label="Рекомендаций" value={results.recommendations.length} /></div></CardContent></Card><div className="space-y-3"><SectionTitle hint={`топ-${Math.min(5, results.recommendations.length)}`}>Рекомендованные программы</SectionTitle>{results.recommendations.slice(0, 5).map((recommendation, index) => <Card data-testid="proftest-result-card" key={recommendation.programId}><CardContent className="flex items-center gap-4 p-4"><div className="flex flex-col items-center"><span className="text-xs text-muted-foreground">#{index + 1}</span><ScoreBadge value={recommendation.contentFit} /></div><div className="min-w-0 flex-1"><p className="font-mono text-xs text-primary">{recommendation.programCode}</p><button onClick={() => navigate({ view: "program", id: recommendation.programId })} className="text-left font-serif font-semibold leading-snug hover:text-primary">{recommendation.programName}</button><p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">{recommendation.reasons[0]?.text}</p></div><Button variant="ghost" size="sm" onClick={() => navigate({ view: "recommendations" })}>Подробности</Button></CardContent></Card>)}</div></div></div>;
}

function componentHint(component: Question["componentType"]): string {
  if (component === "PairChoice") return "Выбери вариант, который ближе; правильного ответа нет.";
  if (component === "ScenarioChoice") return "Представь сценарий и выбери наиболее естественную реакцию.";
  if (component === "AnchoredScale") return "Выбери точку между полюсами шкалы.";
  if (component === "RankTop") return "Выбери и расставь приоритеты среди вариантов.";
  if (component === "ChipSelect") return "Можно выбрать несколько близких вариантов.";
  return "Ответ можно изменить до завершения теста.";
}

function readAnswers(): Record<string, ProftestSessionAnswerRequest> {
  if (typeof window === "undefined") return {};
  try {
    const parsed: unknown = JSON.parse(window.localStorage.getItem(ANSWERS_STORAGE_KEY) ?? "{}");
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
    return Object.fromEntries(Object.entries(parsed).filter(([key, value]) => key.startsWith("core_") || key.startsWith("adaptive_")) ) as Record<string, ProftestSessionAnswerRequest>;
  } catch { return {}; }
}
