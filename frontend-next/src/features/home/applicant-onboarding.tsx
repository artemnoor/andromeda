"use client";

import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, Check, LoaderCircle, Search, Sparkles } from "lucide-react";
import { getUniversityAdmissionBenefits } from "@/lib/api";
import type { components } from "@/lib/generated";
import type { Route } from "@/lib/router";

type Profile = components["schemas"]["ApplicantOnboardingProfileApi-Input"];
type Catalog = components["schemas"]["AdmissionBenefitsResponse"];
type Olympiad = Catalog["olympiads"][number];
type OlympiadProfile = Catalog["olympiadProfiles"][number];
type ResultType = "winner" | "prize_winner" | "team_member";
type SelectedOlympiad = { olympiadId: string; profileId: string | null; resultType: ResultType | null };

const SUBJECTS = [
  "Математика профильная", "Информатика", "Физика", "Обществознание", "Английский язык",
  "История", "Литература", "Химия", "Биология", "География",
] as const;
const ACHIEVEMENTS = ["Волонтёрская деятельность", "Спортивные достижения", "Творческие конкурсы", "Проектная деятельность"] as const;
const YEAR_NOW = 2026;
const RESULT_LABELS: Record<ResultType, string> = { winner: "Победитель", prize_winner: "Призёр", team_member: "Член сборной" };

function Choice({ selected, children, onClick, className = "" }: { selected: boolean; children: React.ReactNode; onClick: () => void; className?: string }) {
  return (
    <button type="button" onClick={onClick} aria-pressed={selected}
      className={`group flex min-h-[62px] w-full items-center justify-between gap-4 rounded-xl border px-4 py-3 text-left transition-colors ${selected ? "border-sky-300/70 bg-sky-300/[0.08] text-white" : "border-white/10 bg-white/[0.025] text-zinc-300 hover:border-white/25 hover:bg-white/[0.055]"} ${className}`}>
      <span>{children}</span><span className={`grid h-5 w-5 shrink-0 place-items-center rounded-full border ${selected ? "border-sky-200 bg-sky-200 text-slate-950" : "border-white/25 text-transparent"}`}><Check className="h-3 w-3" /></span>
    </button>
  );
}

export function ApplicantOnboarding({
  onSave,
  isSaving,
  error,
  navigate,
}: {
  onSave: (profile: Profile) => Promise<unknown>;
  isSaving: boolean;
  error: string | null;
  navigate: (route: Route) => void;
}) {
  const [step, setStep] = useState(0);
  const [grade, setGrade] = useState<number | null>(null);
  const [subjects, setSubjects] = useState<string[]>(["Русский язык"]);
  const [scores, setScores] = useState<Record<string, { value: string; certainty: "known" | "estimated" | null }>>({});
  const [selectedOlympiads, setSelectedOlympiads] = useState<SelectedOlympiad[]>([]);
  const [search, setSearch] = useState("");
  const [catalogs, setCatalogs] = useState<Catalog[]>([]);
  const [catalogBusy, setCatalogBusy] = useState(false);
  const [catalogError, setCatalogError] = useState(false);
  const [catalogRetry, setCatalogRetry] = useState(0);
  const catalogRequestKey = useRef<string | null>(null);
  const [achievements, setAchievements] = useState<string[]>([]);
  const [quota, setQuota] = useState<"special" | "separate" | "unsure" | "none" | null>(null);

  const admissionYear = grade === null ? YEAR_NOW + 1 : YEAR_NOW + 12 - grade;
  useEffect(() => {
    if (step < 4) return;
    const requestKey = `${admissionYear}:${catalogRetry}`;
    if (catalogRequestKey.current === requestKey) return;
    catalogRequestKey.current = requestKey;
    let active = true;
    setCatalogBusy(true);
    setCatalogError(false);
    const years = [...new Set([admissionYear, Math.max(YEAR_NOW + 1, admissionYear - 1), YEAR_NOW + 1, YEAR_NOW])];
    Promise.allSettled(["university:bmstu", "university:hse"].flatMap((universityId) => years.map((year) => getUniversityAdmissionBenefits(universityId, year))))
      .then((results) => {
        if (!active) return;
        const loaded = results.flatMap((result) => result.status === "fulfilled" ? [result.value] : []);
        setCatalogs(loaded.sort((a, b) => b.admissionYear - a.admissionYear));
        setCatalogError(loaded.length === 0);
      })
      .finally(() => { if (active) setCatalogBusy(false); });
    return () => { active = false; };
  }, [admissionYear, catalogRetry, step]);

  const olympiads = useMemo(() => {
    const map = new Map<string, Olympiad>();
    for (const catalog of catalogs) for (const item of catalog.olympiads) {
      const current = map.get(item.id);
      if (!current || item.admissionYear > current.admissionYear) map.set(item.id, item);
    }
    return [...map.values()].sort((a, b) => a.officialName.localeCompare(b.officialName, "ru"));
  }, [catalogs]);
  const profiles = useMemo(() => {
    const map = new Map<string, OlympiadProfile>();
    for (const catalog of catalogs) for (const profile of catalog.olympiadProfiles) {
      const current = map.get(profile.id);
      if (!current || profile.admissionYear > current.admissionYear) map.set(profile.id, profile);
    }
    return [...map.values()];
  }, [catalogs]);
  const filteredOlympiads = useMemo(() => {
    const term = search.trim().toLocaleLowerCase("ru");
    if (!term) return olympiads;
    return olympiads.filter((item) => {
      const profileNames = profiles.filter((profile) => profile.olympiadId === item.id).map((profile) => profile.profileName).join(" ");
      return `${item.officialName} ${item.organizer ?? ""} ${profileNames}`.toLocaleLowerCase("ru").includes(term);
    });
  }, [olympiads, profiles, search]);
  const hasInvalidScore = Object.values(scores).some(({ value, certainty }) => {
    if (!value.trim()) return false;
    const number = Number(value);
    return !Number.isFinite(number) || number < 0 || number > 100 || certainty === null;
  });

  const toggleSubject = (subject: string) => {
    if (subject === "Русский язык") return;
    setSubjects((current) => current.includes(subject) ? current.filter((item) => item !== subject) : [...current, subject]);
  };
  const toggleOlympiad = (item: Olympiad) => {
    setSelectedOlympiads((current) => current.some((selected) => selected.olympiadId === item.id)
      ? current.filter((selected) => selected.olympiadId !== item.id)
      : [...current, { olympiadId: item.id, profileId: null, resultType: null }]);
  };
  const patchOlympiad = (id: string, patch: Partial<SelectedOlympiad>) => setSelectedOlympiads((current) => current.map((item) => item.olympiadId === id ? { ...item, ...patch } : item));
  const goNext = async () => {
    if (step < 7) { setStep((current) => current + 1); return; }
    if (grade === null || quota === null) return;
    const profile: Profile = {
      version: 1,
      grade: grade as 8 | 9 | 10 | 11,
      plannedEgeSubjects: subjects,
      examScores: subjects.map((subject) => {
        const score = scores[subject];
        const hasValue = Boolean(score?.value.trim());
        return { subject, score: hasValue ? Number(score?.value) : null, scoreCertainty: hasValue ? score?.certainty ?? null : null };
      }),
      olympiadResults: selectedOlympiads.map((item) => ({ olympiadId: item.olympiadId, olympiadProfileId: item.profileId, resultType: item.resultType, resultYear: null, gradeOrClass: null })),
      individualAchievements: achievements,
      quotaPreference: quota,
    };
    try {
      await onSave(profile);
      navigate({ view: "catalog" });
    } catch {
      // The context provider exposes the API error inline; keep the answers visible for correction/retry.
    }
  };

  const headings = ["Начало", "Класс", "ЕГЭ", "Баллы", "Олимпиады", "Достижения", "Льготы", "Проверка"];
  return (
    <main className="fixed inset-0 z-[100] min-h-[100dvh] overflow-y-auto bg-[#0b0e13] text-zinc-100 selection:bg-sky-300/30">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-sky-200/50 to-transparent" />
      <div className="mx-auto flex min-h-[100dvh] w-full max-w-6xl flex-col px-5 pb-8 pt-5 sm:px-8 sm:pt-8">
        <header className="flex items-center justify-between border-b border-white/[0.08] pb-5">
          <div className="flex items-center gap-3">
            <Image src="/logo.svg" alt="Andromeda" width={42} height={42} priority className="h-10 w-10 object-contain" />
            <div><div className="text-sm font-semibold tracking-[0.16em] text-white">ANDROMEDA</div><div className="mt-0.5 text-[10px] tracking-[0.2em] text-zinc-500">ОБРАЗОВАТЕЛЬНЫЙ МАРШРУТ</div></div>
          </div>
          {step > 0 && <span className="text-xs tabular-nums text-zinc-500">{step} / 7</span>}
        </header>

        {step > 0 && <nav aria-label="Шаги анкеты" className="mt-6 grid grid-cols-7 gap-1.5 sm:gap-2">
          {headings.slice(1).map((label, index) => <div key={label} className="min-w-0"><div className={`h-1 rounded-full ${index + 1 <= step ? "bg-sky-200" : "bg-white/10"}`} /><span className={`mt-2 hidden truncate text-[10px] sm:block ${index + 1 === step ? "text-sky-100" : "text-zinc-600"}`}>{label}</span></div>)}
        </nav>}

        <section className="mx-auto flex w-full max-w-4xl flex-1 flex-col py-8 sm:py-12" aria-live="polite">
          <div key={step} className="my-auto">
            {step === 0 && <div className="max-w-3xl py-5 sm:py-12">
              <div className="mb-6 flex items-center gap-2 text-xs font-medium tracking-[0.18em] text-sky-200"><Sparkles className="h-4 w-4" /> ВАШ МАРШРУТ ПОСТУПЛЕНИЯ</div>
              <h1 className="max-w-3xl text-4xl font-semibold leading-[1.05] tracking-[-0.04em] sm:text-6xl">Поступление начинается<br className="hidden sm:block" /> с понимания себя.</h1>
              <p className="mt-6 max-w-2xl text-base leading-7 text-zinc-400 sm:text-lg">Ответьте на несколько вопросов — мы учтём ваш класс, планы по ЕГЭ и реальные достижения, чтобы точнее показывать программы и условия поступления.</p>
              <p className="mt-4 text-sm text-zinc-600">Профиль сохранится в вашей сессии. Баллы и олимпиады можно не указывать, если пока не знаете.</p>
            </div>}

            {step === 1 && <Question eyebrow="СЕЙЧАС" title="В каком вы классе?" description="Это поможет определить ориентировочный год поступления." content={<div className="grid grid-cols-2 gap-3 sm:grid-cols-4">{[8, 9, 10, 11].map((value) => <Choice key={value} selected={grade === value} onClick={() => setGrade(value)} className="min-h-24 justify-center text-center text-xl font-medium">{value} класс</Choice>)}</div>} />}

            {step === 2 && <Question eyebrow="ЭКЗАМЕНЫ" title="Какие ЕГЭ планируете сдавать?" description="Выберите предметы, которые уже рассматриваете. Русский язык включён как обязательный." content={<div className="grid gap-2.5 sm:grid-cols-2">{["Русский язык", ...SUBJECTS].map((subject) => <Choice key={subject} selected={subjects.includes(subject)} onClick={() => toggleSubject(subject)} className="min-h-[58px]"> <span className="font-medium">{subject}</span>{subject === "Русский язык" && <span className="ml-2 text-xs text-zinc-500">обязательный</span>}</Choice>)}</div>} />}

            {step === 3 && <Question eyebrow="ОРИЕНТИР ПО БАЛЛАМ" title="На какие баллы ориентируетесь?" description="Для каждого выбранного предмета укажите известный или предполагаемый результат. Неизвестное поле можно оставить пустым." content={<div className="space-y-3">{subjects.map((subject) => { const entry = scores[subject] ?? { value: "", certainty: null }; return <div key={subject} className="rounded-xl border border-white/10 bg-white/[0.025] p-4 sm:flex sm:items-center sm:gap-5"><div className="min-w-0 flex-1"><div className="font-medium">{subject}</div><div className="mt-1 text-xs text-zinc-500">Пустое поле означает, что пока нет оценки</div></div><div className="mt-3 flex flex-col gap-2 sm:mt-0 sm:w-[330px]"><input inputMode="decimal" type="number" min="0" max="100" step="1" value={entry.value} onChange={(event) => setScores((current) => ({ ...current, [subject]: { ...entry, value: event.target.value } }))} placeholder="Баллы от 0 до 100" aria-label={`Баллы ЕГЭ: ${subject}`} className="h-11 w-full rounded-lg border border-white/10 bg-[#10151c] px-3 text-sm text-white outline-none placeholder:text-zinc-600 focus:border-sky-200/70" /><div className="grid grid-cols-2 gap-2">{(["known", "estimated"] as const).map((certainty) => <button key={certainty} type="button" onClick={() => setScores((current) => ({ ...current, [subject]: { ...entry, certainty } }))} className={`rounded-md border px-2 py-2 text-xs transition ${entry.certainty === certainty ? "border-sky-200/60 bg-sky-200/10 text-sky-100" : "border-white/10 text-zinc-500 hover:text-zinc-200"}`}>{certainty === "known" ? "Известен" : "Предполагаемый"}</button>)}</div></div></div>; })}</div>} />}

            {step === 4 && <Question eyebrow="ВАШ ОПЫТ" title="В каких олимпиадах участвуете?" description="Выберите олимпиаду из опубликованных каталогов МГТУ им. Баумана и НИУ ВШЭ. Профиль и результат можно уточнить после выбора." content={<>
              <label className="relative mb-4 block"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Найти олимпиаду по названию" className="h-12 w-full rounded-xl border border-white/10 bg-white/[0.025] pl-10 pr-4 text-sm outline-none placeholder:text-zinc-600 focus:border-sky-200/60" /></label>
              {catalogBusy && <div className="flex items-center gap-2 py-4 text-sm text-zinc-500"><LoaderCircle className="h-4 w-4 animate-spin" /> Загружаем опубликованные каталоги вузов…</div>}
              {catalogError && <div className="rounded-xl border border-amber-200/20 bg-amber-100/[0.04] p-4 text-sm leading-6 text-amber-100/80">Каталоги олимпиад сейчас недоступны. Мы не подставляем демонстрационный список — попробуйте ещё раз.<button type="button" onClick={() => setCatalogRetry((current) => current + 1)} className="ml-2 underline decoration-amber-200/50 underline-offset-4">Повторить</button></div>}
              {!catalogBusy && !catalogError && <><div className="mb-3 flex flex-wrap items-center justify-between gap-2 text-xs text-zinc-500"><span>Найдено в опубликованных источниках: {filteredOlympiads.length}</span><span>Кампании {[...new Set(catalogs.map((item) => item.admissionYear))].join(" · ")}</span></div><div className="max-h-[min(38vh,390px)] space-y-2 overflow-y-auto pr-1">{filteredOlympiads.map((item) => <Choice key={item.id} selected={selectedOlympiads.some((selected) => selected.olympiadId === item.id)} onClick={() => toggleOlympiad(item)} className="min-h-[68px]"><span className="block font-medium leading-5">{item.officialName}</span><span className="mt-1 block text-xs text-zinc-500">{[item.organizer, item.rsoshLevel ? `Уровень ${item.rsoshLevel}` : null, `данные ${item.admissionYear}`].filter(Boolean).join(" · ")}</span></Choice>)}{filteredOlympiads.length === 0 && <p className="rounded-xl border border-dashed border-white/10 py-8 text-center text-sm text-zinc-500">По этому запросу ничего не найдено.</p>}</div></>}
              {selectedOlympiads.map((selected) => { const item = olympiads.find((candidate) => candidate.id === selected.olympiadId); if (!item) return null; const availableProfiles = profiles.filter((profile) => profile.olympiadId === selected.olympiadId); return <div key={selected.olympiadId} className="mt-3 rounded-xl border border-sky-200/20 bg-sky-200/[0.035] p-4"><div className="mb-3 text-sm font-medium">{item.officialName}</div><div className="grid gap-2 sm:grid-cols-2"><label className="text-xs text-zinc-500">Профиль (если известен)<select value={selected.profileId ?? ""} onChange={(event) => patchOlympiad(selected.olympiadId, { profileId: event.target.value || null })} className="mt-1.5 h-10 w-full rounded-lg border border-white/10 bg-[#10151c] px-3 text-sm text-zinc-200"><option value="">Пока не знаю</option>{availableProfiles.map((profile) => <option key={profile.id} value={profile.id}>{profile.profileName}</option>)}</select></label><label className="text-xs text-zinc-500">Результат (необязательно)<select value={selected.resultType ?? ""} onChange={(event) => patchOlympiad(selected.olympiadId, { resultType: (event.target.value || null) as ResultType | null })} className="mt-1.5 h-10 w-full rounded-lg border border-white/10 bg-[#10151c] px-3 text-sm text-zinc-200"><option value="">Пока не знаю</option>{Object.entries(RESULT_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label></div></div>; })}
            </>} />}

            {step === 5 && <Question eyebrow="ДОПОЛНИТЕЛЬНО" title="Есть достижения, которые стоит учесть?" description="Отметьте только то, что действительно относится к вам. Этот список можно будет изменить позже." content={<div className="grid gap-2.5 sm:grid-cols-2">{ACHIEVEMENTS.map((value) => <Choice key={value} selected={achievements.includes(value)} onClick={() => setAchievements((current) => current.includes(value) ? current.filter((item) => item !== value) : [...current, value])} className="min-h-[72px]">{value}</Choice>)}</div>} />}

            {step === 6 && <Question eyebrow="УСЛОВИЯ ПРИЁМА" title="Есть ли у вас право на льготу?" description="Ответ поможет показать подходящие условия. Если пока не знаете — это нормальный ответ." content={<div className="grid gap-2.5 sm:grid-cols-2">{([{ id: "special", label: "Особая квота" }, { id: "separate", label: "Отдельная квота" }, { id: "unsure", label: "Пока не знаю" }, { id: "none", label: "Льгот нет" }] as const).map((item) => <Choice key={item.id} selected={quota === item.id} onClick={() => setQuota(item.id)} className="min-h-[72px]">{item.label}</Choice>)}</div>} />}

            {step === 7 && <Question eyebrow="ПРОВЕРЬТЕ ОТВЕТЫ" title="Всё верно?" description="Профиль останется доступен в этой сессии. Его можно дополнить позже." content={<div className="space-y-3">{[
              ["Класс", grade ? `${grade} класс` : "—"],
              ["ЕГЭ", subjects.join(" · ")],
              ["Баллы", Object.entries(scores).filter(([, value]) => value.value.trim()).map(([subject, value]) => `${subject}: ${value.value} (${value.certainty === "known" ? "известен" : "предполагаемый"})`).join(" · ") || "Пока не указаны"],
              ["Олимпиады", selectedOlympiads.map((entry) => olympiads.find((item) => item.id === entry.olympiadId)?.officialName).filter(Boolean).join(" · ") || "Пока не выбраны"],
              ["Достижения", achievements.join(" · ") || "Пока не выбраны"],
              ["Льгота", quota === "unsure" ? "Пока не знаю" : quota === "none" ? "Льгот нет" : quota === "special" ? "Особая квота" : quota === "separate" ? "Отдельная квота" : "—"],
            ].map(([label, value]) => <div key={label} className="grid gap-1 border-b border-white/[0.08] py-3 sm:grid-cols-[150px_1fr]"><span className="text-xs uppercase tracking-[0.12em] text-zinc-500">{label}</span><span className="text-sm leading-6 text-zinc-200">{value}</span></div>)}</div>} />}
          </div>
        </section>

        <footer className="sticky bottom-0 mt-4 border-t border-white/[0.08] bg-[#0b0e13]/95 py-4 backdrop-blur sm:py-5">
          {error && <p role="alert" className="mx-auto mb-3 max-w-4xl text-sm text-rose-300">{error}</p>}
          <div className="mx-auto flex max-w-4xl items-center justify-between gap-3">
            {step > 0 ? <button type="button" onClick={() => setStep((current) => current - 1)} className="inline-flex min-h-11 items-center gap-2 bg-transparent px-1 text-sm text-zinc-400 transition hover:text-white"><ArrowLeft className="h-4 w-4" /> Назад</button> : <button type="button" onClick={() => navigate({ view: "catalog" })} className="min-h-11 bg-transparent px-1 text-sm text-zinc-500 transition hover:text-zinc-200">Сначала посмотреть каталог</button>}
            <button type="button" onClick={() => void goNext()} disabled={(step === 1 && grade === null) || (step === 3 && hasInvalidScore) || (step === 6 && quota === null) || isSaving} className="inline-flex min-h-11 items-center gap-2 bg-transparent px-1 text-sm font-medium text-sky-100 transition hover:text-white disabled:cursor-not-allowed disabled:text-zinc-600">
              {isSaving ? <><LoaderCircle className="h-4 w-4 animate-spin" /> Сохраняем…</> : <>{step === 7 ? "Сохранить профиль" : step === 0 ? "Продолжить" : "Продолжить"}<ArrowRight className="h-4 w-4" /></>}
            </button>
          </div>
        </footer>
      </div>
    </main>
  );
}

function Question({ eyebrow, title, description, content }: { eyebrow: string; title: string; description: string; content: React.ReactNode }) {
  return <div><p className="mb-3 text-xs font-medium tracking-[0.16em] text-sky-200">{eyebrow}</p><h1 className="max-w-3xl text-3xl font-semibold leading-tight tracking-[-0.035em] sm:text-5xl">{title}</h1><p className="mt-4 max-w-2xl text-sm leading-6 text-zinc-400 sm:text-base">{description}</p><div className="mt-8">{content}</div></div>;
}
