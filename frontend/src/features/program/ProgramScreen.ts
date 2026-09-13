import { getProgramAdmissions, type ProgramAdmissionsResponse } from "../../api/client";
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
    <p class="provenance">Официальная программа МГТУ · <a href="${escapeAttribute(response.program.sourceUrl)}" target="_blank" rel="noreferrer">учебный план</a></p>
    <div id="program-admissions"></div>
    <div id="program-admission-fit"></div>
  `;
  const admissionsRoot = root.querySelector<HTMLElement>("#program-admissions");
  const admissionFitRoot = root.querySelector<HTMLElement>("#program-admission-fit");
  if (!admissionsRoot || !admissionFitRoot) return;
  renderAdmissionsLoading(admissionsRoot);
  renderAdmissionFitLoading(admissionFitRoot);
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

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}

function escapeAttribute(value: string): string {
  return escapeHtml(value);
}
