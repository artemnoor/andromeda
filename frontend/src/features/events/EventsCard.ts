import type { EventResponse } from "../../api/client";
import type { components } from "../../api/generated";

type Program = components["schemas"]["ProgramSummaryResponse"];
type Event = EventResponse["event"];

const kindLabels: Record<components["schemas"]["EventKind"], string> = {
  additional_education: "ДОД",
  open_day: "День открытых дверей",
  lecture: "Лекция",
  competition: "Конкурс",
  career: "Карьера",
  other: "Событие",
};

const formatLabels: Record<components["schemas"]["EventFormat"], string> = {
  offline: "Очно",
  online: "Онлайн",
  hybrid: "Гибрид",
};

export function renderEventCard(event: Event, programs: readonly Program[]): string {
  const date = formatDate(event.startsAt);
  const programLabels = event.programIds.map((id) => {
    const program = programs.find((item) => item.id === id);
    return program ? `${program.code} · ${program.name}` : id;
  });
  const links = `<div class="event-links"><span class="label">Связи</span><p>Университет: ${event.universityIds.map(escapeHtml).join(", ")}</p>${event.departmentIds.length > 0 ? `<p>Кафедра: ${event.departmentIds.map(escapeHtml).join(", ")}</p>` : ""}${event.programIds.length > 0 ? `<ul>${programLabels.map((label) => `<li>${escapeHtml(label)}</li>`).join("")}</ul>` : `<p>Университетское событие</p>`}</div>`;
  const venue = event.venue ? `<div class="event-venue"><span class="label">Место</span><p>${escapeHtml(event.venue.name)}</p>${event.venue.address ? `<p>${escapeHtml(event.venue.address)}</p>` : ""}${event.venue.latitude !== null && event.venue.longitude !== null ? `<p data-testid="event-coordinates">Координаты: ${escapeHtml(String(event.venue.latitude))}, ${escapeHtml(String(event.venue.longitude))}</p>` : ""}</div>` : `<div class="event-venue"><span class="label">Место</span><p>Онлайн</p></div>`;
  const registration = event.registrationUrl ? `<a class="secondary-button" data-testid="event-registration" href="${safeHref(event.registrationUrl)}" target="_blank" rel="noreferrer">Регистрация</a>` : "";
  return `<article class="event-card" data-testid="event-card" data-event-id="${escapeHtml(event.id)}"><div class="event-card-meta"><span class="status">${escapeHtml(kindLabels[event.kind])}</span><span class="status">${escapeHtml(formatLabels[event.format])}</span></div><h3>${escapeHtml(event.title)}</h3><time data-testid="event-date" datetime="${escapeHtml(event.startsAt)}">${escapeHtml(date)}</time>${event.description ? `<p class="event-description">${escapeHtml(event.description)}</p>` : ""}<div class="event-card-details">${links}${venue}</div><div class="event-card-actions"><a class="text-link" data-testid="event-detail-link" href="#event/${encodeURIComponent(event.id)}">Подробнее <span aria-hidden="true">→</span></a>${registration}<code>${escapeHtml(event.id)}</code></div></article>`;
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ru-RU", { dateStyle: "long", timeStyle: "short" }).format(date);
}

function safeHref(value: string): string {
  try {
    const base = typeof window === "undefined" ? "http://localhost/" : window.location.origin;
    const url = new URL(value, base);
    return url.protocol === "http:" || url.protocol === "https:" ? escapeHtml(url.href) : "#";
  } catch {
    return "#";
  }
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
