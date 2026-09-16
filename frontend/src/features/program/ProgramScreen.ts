import { getCurriculum, getProgramAdmissions, type CurriculumResponse, type ProgramAdmissionsResponse } from "../../api/client";
import { ApiError } from "../../api/errors";
import { renderAdmissions, renderAdmissionsError, renderAdmissionsLoading } from "../admissions/AdmissionsBlock";
import { renderAdmissionFit, renderAdmissionFitError, renderAdmissionFitLoading } from "../admission-fit/AdmissionFitBlock";
import type { ProgramResponse } from "../../api/client";

export function renderProgramScreen(root: HTMLElement, response: ProgramResponse): void {
  root.innerHTML = `
    <section class="hero">
      <p class="eyebrow">Источник данных · BMSTU</p>
      <h1>${escapeHtml(response.program.name)}</h1>
      <p class="lead">${escapeHtml(response.program.code)} · ${response.program.educationYear}</p>
    </section>
    <section class="identity-grid" aria-label="Карточка программы">
      <article class="card"><span class="label">Направление</span><strong>${escapeHtml(response.program.directionId)}</strong><span>МГТУ им. Н.Э. Баумана</span></article>
      <article class="card"><span class="label">Год набора</span><strong>${response.program.educationYear}</strong><span>Учебный план доступен</span></article>
      <article class="card"><span class="label">Контракт</span><strong>Проверен</strong><span>Ответ прошёл API schema</span></article>
    </section>
    <p class="provenance">Официальная программа МГТУ · <a href="${escapeAttribute(response.program.sourceUrl)}" target="_blank" rel="noreferrer">карточка источника</a> · <a href="${escapeAttribute(response.program.studyPlanUrl)}" target="_blank" rel="noreferrer">документ учебного плана</a></p>
    <div id="program-curriculum"></div>
    <div id="program-admissions"></div>
    <div id="program-admission-fit"></div>
  `;
  const admissionsRoot = root.querySelector<HTMLElement>("#program-admissions");
  const curriculumRoot = root.querySelector<HTMLElement>("#program-curriculum");
  const admissionFitRoot = root.querySelector<HTMLElement>("#program-admission-fit");
  if (!admissionsRoot || !curriculumRoot || !admissionFitRoot) return;
  renderCurriculumLoading(curriculumRoot);
  renderAdmissionsLoading(admissionsRoot);
  renderAdmissionFitLoading(admissionFitRoot);
  void getCurriculum(response.program.id)
    .then((curriculum) => renderCurriculum(curriculumRoot, curriculum))
    .catch((error: unknown) => renderCurriculumError(curriculumRoot, error instanceof ApiError ? error.payload.message : "Не удалось получить учебный план"));
  void getProgramAdmissions(response.program.id)
    .then((admissions: ProgramAdmissionsResponse) => {
      renderAdmissions(admissionsRoot, admissions);
      renderAdmissionFit(admissionFitRoot, response.program.id, admissions);
    })
    .catch((error: unknown) => {
      const message = error instanceof ApiError ? `${error.payload.code}: ${error.payload.message}` : "Не удалось получить данные поступления";
      renderAdmissionsError(admissionsRoot, message);
      renderAdmissionFitError(admissionFitRoot, message);
    });
}

function renderCurriculumLoading(root: HTMLElement): void {
  root.innerHTML = '<section class="curriculum-section state-card" data-testid="curriculum" aria-live="polite"><p class="loading">Загружаем учебный план…</p></section>';
}

function renderCurriculumError(root: HTMLElement, message: string): void {
  root.innerHTML = `<section class="curriculum-section state-card error-state" data-testid="curriculum" role="alert"><p class="eyebrow">Учебный план</p><h2>Не удалось загрузить curriculum</h2><p class="muted">${escapeHtml(message)}</p></section>`;
}

function renderCurriculum(root: HTMLElement, response: CurriculumResponse): void {
  const rows = response.items.map((item) => `<tr><th scope="row">${escapeHtml(item.discipline.name)}</th><td>${item.semester ?? "—"}</td><td>${item.hours} ч</td><td>${escapeHtml(item.credits ?? "—")}</td><td>${escapeHtml(item.assessmentTypes?.join(", ") ?? "—")}</td></tr>`).join("");
  root.innerHTML = `<section class="curriculum-section" data-testid="curriculum" aria-labelledby="curriculum-title"><div class="section-heading"><div><p class="eyebrow">Содержание программы</p><h2 id="curriculum-title">Учебный план</h2><p class="muted">${response.items.length} дисциплин из источника ${response.educationYear} года.</p></div><a class="text-link" href="${escapeAttribute(response.sourceUrl)}" target="_blank" rel="noreferrer">Открыть источник <span aria-hidden="true">↗</span></a></div><div class="curriculum-table-wrap"><table class="curriculum-table"><thead><tr><th scope="col">Дисциплина</th><th scope="col">Семестр</th><th scope="col">Часы</th><th scope="col">ЗЕТ</th><th scope="col">Контроль</th></tr></thead><tbody>${rows || '<tr><td colspan="5">Учебные элементы пока не опубликованы.</td></tr>'}</tbody></table></div></section>`;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}

function escapeAttribute(value: string): string {
  return escapeHtml(value);
}
