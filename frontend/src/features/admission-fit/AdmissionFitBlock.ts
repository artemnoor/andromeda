import {
  calculateAdmissionFit,
  type AdmissionFitRequest,
  type AdmissionFitResponse,
  type ProgramAdmissionsResponse,
} from "../../api/client";
import { ApiError } from "../../api/errors";

type Offering = ProgramAdmissionsResponse["offerings"][number];
type Reason = AdmissionFitResponse["reasons"][number];
type Metric = AdmissionFitResponse["breakdown"]["minimumReadiness"];

const fundingLabels: Record<NonNullable<Offering["fundingType"]>, string> = {
  budget: "Бюджет",
  paid: "Платное",
  targeted: "Целевой набор",
  unknown: "Финансирование не указано",
};

const formLabels: Record<NonNullable<Offering["studyForm"]>, string> = {
  full_time: "Очная форма",
  part_time: "Заочная форма",
  evening: "Очно-заочная форма",
  online: "Онлайн",
  unknown: "Форма не указана",
};

const statusLabels: Record<AdmissionFitResponse["status"], string> = {
  realistic: "Реалистично",
  borderline: "Погранично",
  unlikely: "Низкая реалистичность",
  insufficient_data: "Недостаточно данных",
};

const metricStatusLabels: Record<Metric["status"], string> = {
  available: "Достаточно данных",
  partial: "Частично",
  not_available: "Нет данных",
};

export function renderAdmissionFitLoading(root: HTMLElement): void {
  root.innerHTML = '<section class="state-card admission-fit-state" aria-live="polite"><p class="loading">Готовим расчёт Admission Fit…</p></section>';
}

export function renderAdmissionFitError(root: HTMLElement, message = "Не удалось загрузить расчёт Admission Fit"): void {
  root.innerHTML = '<section class="state-card admission-fit-state error-state" role="alert"><p class="eyebrow">Admission Fit</p><h3>Не удалось подготовить расчёт</h3><p class="muted">' + escapeHtml(message) + '</p><p class="muted">Проверьте доступность API и обновите страницу.</p></section>';
}

export function renderAdmissionFitEmpty(root: HTMLElement): void {
  root.innerHTML = '<section class="state-card admission-fit-state"><p class="eyebrow">Admission Fit</p><h3>Недостаточно данных для расчёта</h3><p class="muted">Для этой программы нет опубликованных требований к экзаменам. Мы не подменяем отсутствующие данные предположениями.</p></section>';
}

export function renderAdmissionFit(root: HTMLElement, programId: string, response: ProgramAdmissionsResponse): void {
  const offerings = response.offerings.filter((offering) => offering.exams.length > 0);
  if (offerings.length === 0) {
    renderAdmissionFitEmpty(root);
    return;
  }

  let selectedOfferingId = offerings[0]?.id ?? "";
  let submitting = false;
  const drafts = new Map<string, string>();

  root.innerHTML = '<section class="admission-fit-section" aria-labelledby="admission-fit-title" data-testid="admission-fit"><div class="section-heading admission-fit-heading"><div><p class="eyebrow">Отдельный показатель</p><h2 id="admission-fit-title">Admission Fit</h2></div><span class="count">не влияет на Content Fit</span></div><p class="muted admission-fit-intro">Введите свои баллы и сравните их с опубликованными требованиями выбранного набора. Это оценка реалистичности по доступным данным, а не гарантия поступления.</p><form class="admission-fit-form" data-testid="admission-fit-form"></form><div class="admission-fit-result" data-testid="admission-fit-result" aria-live="polite"></div></section>';
  const formElement = root.querySelector<HTMLFormElement>("[data-testid='admission-fit-form']");
  const resultElement = root.querySelector<HTMLElement>("[data-testid='admission-fit-result']");
  if (!formElement || !resultElement) return;
  const form = formElement;
  const resultRoot = resultElement;

  renderForm();
  renderResultIdle();

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (submitting) return;
    const offering = selectedOffering();
    if (!offering) return;
    const scores = Array.from(form.querySelectorAll<HTMLInputElement>("[data-admission-score]"))
      .map((input) => ({ subject: input.dataset.subject ?? "", rawScore: input.value.trim() }))
      .filter((item) => item.subject && item.rawScore !== "")
      .map((item) => ({ subject: item.subject, score: Number(item.rawScore) }))
      .filter((item) => Number.isFinite(item.score));
    const request: AdmissionFitRequest = {
      version: 1,
      offeringId: offering.id,
      applicant: { version: 1, scores },
    };
    submitting = true;
    setSubmitState();
    renderResultLoading();
    void calculateAdmissionFit(programId, request)
      .then((fit) => {
        submitting = false;
        setSubmitState();
        renderResult(fit);
      })
      .catch((error: unknown) => {
        submitting = false;
        setSubmitState();
        const message = error instanceof ApiError ? error.payload.message : "Не удалось рассчитать Admission Fit";
        resultRoot.innerHTML = '<section class="admission-fit-result-card error-state" role="alert"><h3>Расчёт не выполнен</h3><p class="muted">' + escapeHtml(message) + '</p><button class="secondary-button" type="button" data-testid="admission-fit-retry">Повторить</button></section>';
        resultRoot.querySelector<HTMLButtonElement>("[data-testid='admission-fit-retry']")?.addEventListener("click", () => {
          form.requestSubmit();
        });
      });
  });

  function selectedOffering(): Offering | undefined {
    return offerings.find((offering) => offering.id === selectedOfferingId);
  }

  function renderForm(): void {
    const offering = selectedOffering();
    if (!offering) return;
    const exams = uniqueExams(offering);
    const title = [
      String(offering.admissionYear),
      offering.fundingType ? fundingLabels[offering.fundingType] : "",
      offering.studyForm ? formLabels[offering.studyForm] : "",
      offering.scope === "direction" ? "по направлению" : "по программе",
    ].filter(Boolean).join(" · ");
    form.innerHTML = '<div class="admission-fit-form-grid"><label><span>Набор для сравнения</span><select data-testid="admission-fit-offering">' + offerings.map((item) => offeringOption(item, selectedOfferingId)).join("") + '</select></label><div class="admission-fit-form-copy"><span class="label">Что сравниваем</span><strong>' + escapeHtml(title) + '</strong><small>Источник требований — карточка выбранного offering.</small></div></div><div class="admission-fit-score-grid">' + exams.map((exam) => scoreField(exam, drafts.get(draftKey(offering.id, exam.subject)) ?? "")).join("") + '</div><button class="primary-button admission-fit-submit" type="submit" data-testid="admission-fit-submit">Рассчитать Admission Fit</button>';
    const select = form.querySelector<HTMLSelectElement>("[data-testid='admission-fit-offering']");
    select?.addEventListener("change", () => {
      selectedOfferingId = select.value;
      renderForm();
      renderResultIdle();
    });
    form.querySelectorAll<HTMLInputElement>("[data-admission-score]").forEach((input) => {
      input.addEventListener("input", () => {
        const subject = input.dataset.subject ?? "";
        drafts.set(draftKey(selectedOfferingId, subject), input.value);
      });
    });
    setSubmitState();
  }

  function setSubmitState(): void {
    const submit = form.querySelector<HTMLButtonElement>("[data-testid='admission-fit-submit']");
    if (submit) submit.disabled = submitting;
  }

  function renderResultIdle(): void {
    resultRoot.innerHTML = '<p class="muted admission-fit-result-hint">Заполните известные вам баллы. Пустое поле останется незаполненным и попадёт в объяснение как пробел данных.</p>';
  }

  function renderResultLoading(): void {
    resultRoot.innerHTML = '<section class="admission-fit-result-card" aria-live="polite"><p class="loading">Считаем по требованиям выбранного набора…</p></section>';
  }

  function renderResult(fit: AdmissionFitResponse): void {
    resultRoot.innerHTML = '<section class="admission-fit-result-card" data-testid="admission-fit-success"><div class="admission-fit-result-head"><div><p class="eyebrow">Результат по опубликованным данным</p><h3>' + escapeHtml(statusLabels[fit.status]) + '</h3><p class="muted">Качество данных: ' + escapeHtml(dataQualityLabel(fit.dataQuality)) + '</p></div><div class="admission-fit-score"><strong data-testid="admission-fit-score">' + String(fit.score) + '</strong><span>из 100</span></div></div><div class="admission-fit-metrics">' + metricCard("Минимумы", fit.breakdown.minimumReadiness) + metricCard("Проходной балл", fit.breakdown.passingReadiness) + metricCard("Полнота баллов", fit.breakdown.dataCompleteness) + '</div><div class="admission-fit-reasons">' + reasonSection("Что совпало", fit.reasons, "positive", "+") + reasonSection("Что снижает оценку", fit.antiReasons, "negative", "−") + reasonSection("Каких данных не хватает", fit.dataGaps, "data-gap", "·") + '</div></section>';
  }

  function metricCard(label: string, metric: Metric): string {
    const value = metric.value === null || metric.value === undefined ? "—" : formatDecimal(metric.value) + "%";
    return '<article class="admission-fit-metric"><span class="label">' + escapeHtml(label) + '</span><strong>' + value + '</strong><small>' + escapeHtml(metricStatusLabels[metric.status]) + '</small></article>';
  }

  function reasonSection(title: string, reasons: readonly Reason[], className: string, marker: string): string {
    if (reasons.length === 0) return "";
    return '<section class="admission-fit-reason-group ' + className + '"><h4>' + escapeHtml(title) + '</h4><ul>' + reasons.map((reason) => '<li><span class="admission-fit-reason-marker">' + marker + '</span><div><strong>' + escapeHtml(reason.message) + '</strong>' + evidence(reason) + '</div></li>').join("") + '</ul></section>';
  }

  function evidence(reason: Reason): string {
    const facts: string[] = [];
    if (reason.applicantScore !== null && reason.applicantScore !== undefined) facts.push("Ваш балл: " + formatDecimal(reason.applicantScore));
    if (reason.applicantTotalScore !== null && reason.applicantTotalScore !== undefined) facts.push("Ваша сумма: " + formatDecimal(reason.applicantTotalScore));
    if (reason.referenceScore !== null && reason.referenceScore !== undefined) facts.push("Ориентир: " + formatDecimal(reason.referenceScore));
    const source = reason.provenance[0];
    const sourceMarkup = source ? ' · <a href="' + escapeAttribute(source.sourceUrl) + '" target="_blank" rel="noreferrer">' + escapeHtml(reason.sourceName ?? source.sourceName ?? source.sourceKind) + '</a>' : "";
    return '<small>' + escapeHtml(facts.join(" · ")) + sourceMarkup + '</small>';
  }
}

function uniqueExams(offering: Offering): Offering["exams"] {
  const seen = new Set<string>();
  return offering.exams.filter((exam) => {
    const key = exam.subject.toLocaleLowerCase("ru-RU").replace(/\s+/g, " ").trim();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function offeringOption(offering: Offering, selectedId: string): string {
  const title = [
    String(offering.admissionYear),
    offering.fundingType ? fundingLabels[offering.fundingType] : "",
    offering.studyForm ? formLabels[offering.studyForm] : "",
    offering.scope === "direction" ? "по направлению" : "по программе",
  ].filter(Boolean).join(" · ");
  const selected = offering.id === selectedId ? " selected" : "";
  return '<option value="' + escapeAttribute(offering.id) + '"' + selected + '>' + escapeHtml(title) + '</option>';
}

function scoreField(exam: Offering["exams"][number], value: string): string {
  const minimum = exam.minimumScore === null || exam.minimumScore === undefined ? "минимум не опубликован" : "минимум " + formatDecimal(exam.minimumScore);
  return '<label class="admission-fit-score-field"><span>' + escapeHtml(exam.subject) + (exam.isChoice ? " · на выбор" : "") + '</span><input type="number" min="0" max="100" step="0.01" inputmode="decimal" data-admission-score data-subject="' + escapeAttribute(exam.subject) + '" value="' + escapeAttribute(value) + '" aria-label="Баллы: ' + escapeAttribute(exam.subject) + '"><small>' + escapeHtml(minimum) + '</small></label>';
}

function draftKey(offeringId: string, subject: string): string {
  return offeringId + "::" + subject;
}

function dataQualityLabel(value: AdmissionFitResponse["dataQuality"]): string {
  return value === "complete" ? "полное" : value === "partial" ? "частичное" : "недоступное";
}

function formatDecimal(value: string): string {
  return Number(value).toLocaleString("ru-RU", { maximumFractionDigits: 2 });
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}

function escapeAttribute(value: string): string {
  return escapeHtml(value);
}
