import type { ProgramAdmissionsResponse } from "../../api/client";

type Offering = ProgramAdmissionsResponse["offerings"][number];

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

const scoreLabels: Record<Offering["passingScores"][number]["scoreType"], string> = {
  budget: "Проходной на бюджет",
  paid: "Проходной на платное",
  average: "Средний проходной",
  other: "Проходной балл",
};

const competitionLabels: Record<string, string> = {
  general: "Общий конкурс",
  special_quota: "Особая квота",
  separate_quota: "Отдельная квота",
  targeted: "Целевая квота",
  bvi: "БВИ",
  other: "Другой конкурс",
};

const quotaLabels: Record<Offering["quotas"][number]["quotaType"], string> = {
  special: "Особая квота",
  separate: "Отдельная квота",
  targeted: "Целевой набор",
  other: "Квота",
};

export function renderAdmissionsLoading(root: HTMLElement): void {
  root.innerHTML = '<section class="state-card admissions-state" aria-live="polite"><p class="loading">Загружаем данные поступления…</p></section>';
}

export function renderAdmissionsError(root: HTMLElement, message = "Не удалось получить данные поступления"): void {
  root.innerHTML = `<section class="state-card admissions-state error-state" role="alert"><p class="eyebrow">Данные поступления</p><h3>Не удалось загрузить раздел</h3><p class="muted">${escapeHtml(message)}</p><p class="muted">Попробуйте обновить страницу или проверить доступность API.</p></section>`;
}

export function renderAdmissionsEmpty(root: HTMLElement): void {
  root.innerHTML = '<section class="state-card admissions-state"><p class="eyebrow">Данные поступления</p><h3>Пока нет опубликованных данных</h3><p class="muted">Для этой программы в источниках МГТУ не найден набор admissions. Мы не подменяем отсутствующие значения догадками.</p></section>';
}

export function renderAdmissions(root: HTMLElement, response: ProgramAdmissionsResponse): void {
  if (response.offerings.length === 0) {
    renderAdmissionsEmpty(root);
    return;
  }
  root.innerHTML = `<section class="admissions-section" aria-labelledby="admissions-title"><div class="section-heading"><div><p class="eyebrow">Официальные данные МГТУ</p><h2 id="admissions-title">Поступление</h2></div><span class="count">${response.offerings.length} записей</span></div><p class="muted admissions-intro">Данные привязаны к канонической программе и показаны с указанием года и источника. Числовой минимум — наименьшая сумма баллов среди опубликованных зачисленных и включает индивидуальные достижения; это не гарантия будущего проходного балла. Экзаменационные минимумы ниже — отдельные требования допуска.</p><div class="admissions-grid">${response.offerings.map(renderOffering).join("")}</div></section>`;
}

function renderOffering(offering: Offering): string {
  const title = [String(offering.admissionYear), offering.fundingType ? fundingLabels[offering.fundingType] : "", offering.studyForm ? formLabels[offering.studyForm] : ""].filter(Boolean).join(" · ");
  const scoreRows = offering.passingScores.map(renderPassingScore).join("");
  const examRows = offering.exams.map((exam) => `<li><span>${escapeHtml(exam.subject)}${exam.isChoice ? " · на выбор" : ""}</span><strong>${exam.minimumScore === null || exam.minimumScore === undefined ? "—" : `${formatDecimal(exam.minimumScore)} мин.`}</strong></li>`).join("");
  const quotaRows = offering.quotas.map((quota) => `<li><span>${quotaLabels[quota.quotaType]}</span><strong>${quota.places} мест</strong></li>`).join("");
  const tuitionRows = offering.tuition.map((tuition) => `<li><span>${tuition.isDiscounted ? "Со скидкой" : "Стоимость"}${tuition.period ? ` · ${escapeHtml(tuition.period)}` : ""}</span><strong>${formatMoney(tuition.amount, tuition.currency)}</strong></li>`).join("");
  return `<article class="admission-card"><div class="admission-card-head"><div><span class="label">${offering.scope === "direction" ? "По направлению" : "По программе"}</span><h3>${escapeHtml(title)}</h3></div>${offering.places === null || offering.places === undefined ? "" : `<div class="admission-places"><strong>${offering.places}</strong><span>мест</span></div>`}</div>${scoreRows ? `<div class="admission-group"><h4>Проходные баллы</h4><ul>${scoreRows}</ul></div>` : ""}${examRows ? `<div class="admission-group"><h4>ЕГЭ и минимумы</h4><ul>${examRows}</ul></div>` : ""}${quotaRows ? `<div class="admission-group"><h4>Квоты</h4><ul>${quotaRows}</ul></div>` : ""}${tuitionRows ? `<div class="admission-group"><h4>Стоимость обучения</h4><ul>${tuitionRows}</ul></div>` : ""}<p class="admission-source">Источник: <a href="${escapeAttribute(offering.provenance[0]?.sourceUrl ?? "#")}" target="_blank" rel="noreferrer">${escapeHtml(offering.provenance[0]?.sourceName ?? offering.provenance[0]?.sourceKind ?? "официальный источник")}</a></p></article>`;
}

function renderPassingScore(score: Offering["passingScores"][number]): string {
  const route = competitionLabels[score.competitionType ?? "other"] ?? "Другой конкурс";
  const kind = scoreLabels[score.scoreType] ?? "Проходной балл";
  if (score.status === "bvi") {
    return `<li><span>${escapeHtml(route)} · ${escapeHtml(kind)}</span><strong>БВИ (без вступительных испытаний)</strong></li>`;
  }
  if (score.score === null || score.score === undefined) {
    return `<li><span>${escapeHtml(route)} · ${escapeHtml(kind)}</span><strong>Не опубликован</strong></li>`;
  }
  return `<li><span>${escapeHtml(route)} · ${escapeHtml(kind)}</span><strong>Минимум зачисленных: ${formatDecimal(score.score)} баллов</strong></li>`;
}

function formatDecimal(value: string): string {
  return Number(value).toLocaleString("ru-RU", { maximumFractionDigits: 2 });
}

function formatMoney(value: string, currency: string): string {
  return `${formatDecimal(value)} ${currency === "RUB" ? "₽" : escapeHtml(currency)}`;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}

function escapeAttribute(value: string): string {
  return escapeHtml(value);
}
