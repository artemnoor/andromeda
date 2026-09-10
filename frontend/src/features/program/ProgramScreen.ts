import type { ProgramResponse } from "../../api/client";

export function renderProgramScreen(root: HTMLElement, response: ProgramResponse): void {
  root.innerHTML = `
    <section class="hero">
      <p class="eyebrow">Источник данных · BMSTU</p>
      <h1>${escapeHtml(response.program.name)}</h1>
      <p class="lead">${escapeHtml(response.direction.code)} · ${escapeHtml(response.direction.name)}</p>
    </section>
    <section class="identity-grid" aria-label="Карточка программы">
      <article class="card"><span class="label">Университет</span><strong>${escapeHtml(response.university.name)}</strong><span>${escapeHtml(response.university.city)}</span></article>
      <article class="card"><span class="label">Год набора</span><strong>${response.program.educationYear}</strong><span>${escapeHtml(response.direction.educationLevel)}</span></article>
      <article class="card"><span class="label">Контракт</span><strong>Проверен</strong><span>Ответ прошёл API schema</span></article>
    </section>
    <p class="provenance">Снимок: <code>${escapeHtml(response.source.contentSha256.slice(0, 12))}…</code> · <a href="${escapeAttribute(response.source.url)}" target="_blank" rel="noreferrer">официальный источник</a></p>
  `;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}

function escapeAttribute(value: string): string {
  return escapeHtml(value);
}
