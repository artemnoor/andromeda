import { getCampusPoint, getCampusPointEvents, getEvent, type CampusPointEventsResponse, type CampusPointResponse } from "../../api/client";
import { ApiError } from "../../api/errors";
import type { components } from "../../api/generated";

type Program = components["schemas"]["ProgramSummaryResponse"];
type Event = components["schemas"]["EventResponse"];

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

export function renderEventPage(root: HTMLElement, eventId: string, programs: readonly Program[]): void {
  root.innerHTML = `<section class="hero compact event-detail-hero"><div class="hero-kicker"><span class="eyebrow">Andromeda · событие</span><span class="hero-index">07 / 10</span></div><a class="back-link" href="#events">← Все события</a></section><main id="event-detail-content" aria-live="polite"><section class="state-card" data-testid="event-detail-loading" role="status"><p class="eyebrow">Событие</p><h2>Загружаем детали…</h2><p>Проверяем дату, регистрацию и место проведения.</p></section></main>`;
  const content = root.querySelector<HTMLElement>("#event-detail-content");
  if (!content) return;
  void getEvent(eventId).then((response) => {
    const event = response.event;
    content.innerHTML = renderEventDetail(event, programs);
    void loadCampusContext(content, event);
  }).catch((error: unknown) => {
    const message = error instanceof ApiError ? error.payload.message : "Не удалось получить событие";
    content.innerHTML = `<section class="state-card error-state" data-testid="event-detail-error" role="alert"><p class="eyebrow">Ошибка API</p><h2>${escapeHtml(message)}</h2><p>Вернись к списку событий и попробуй открыть карточку ещё раз.</p><a class="secondary-button" href="#events">Вернуться к событиям</a></section>`;
  });
}

function renderEventDetail(event: Event, programs: readonly Program[]): string {
  const linkedPrograms = event.programIds.map((id) => programs.find((program) => program.id === id)).filter((program): program is Program => Boolean(program));
  const venue = event.venue ? `<div class="event-detail-fact"><span class="label">Место</span><strong>${escapeHtml(event.venue.name)}</strong>${event.venue.address ? `<span>${escapeHtml(event.venue.address)}</span>` : ""}${event.venue.latitude !== null && event.venue.latitude !== undefined && event.venue.longitude !== null && event.venue.longitude !== undefined ? `<small>Координаты: ${escapeHtml(String(event.venue.latitude))}, ${escapeHtml(String(event.venue.longitude))}</small>` : ""}</div>` : `<div class="event-detail-fact"><span class="label">Место</span><strong>Онлайн</strong><span>Точка проведения не указана в источнике.</span></div>`;
  const registration = event.registrationUrl ? `<a class="primary-button" data-testid="event-detail-registration" href="${safeHref(event.registrationUrl)}" target="_blank" rel="noreferrer">Зарегистрироваться</a>` : "";
  return `<article class="event-detail-card" data-testid="event-detail"><div class="event-detail-meta"><span class="status">${escapeHtml(kindLabels[event.kind])}</span><span class="status">${escapeHtml(formatLabels[event.format])}</span></div><h1 data-testid="event-detail-title">${escapeHtml(event.title)}</h1><p class="event-detail-description">${escapeHtml(event.description ?? "Описание события пока не опубликовано.")}</p><div class="event-detail-actions">${registration}<a class="secondary-button" href="#events">Смотреть другие события</a></div><div class="event-detail-facts"><div class="event-detail-fact"><span class="label">Когда</span><strong><time datetime="${escapeHtml(event.startsAt)}">${escapeHtml(formatDate(event.startsAt))}</time></strong>${event.endsAt ? `<span>до ${escapeHtml(formatDate(event.endsAt))}</span>` : ""}</div>${venue}<div class="event-detail-fact"><span class="label">Для кого</span>${linkedPrograms.length > 0 ? linkedPrograms.map((program) => `<a href="#program/${encodeURIComponent(program.id)}">${escapeHtml(program.code)} · ${escapeHtml(program.name)}</a>`).join("") : `<strong>Для всех абитуриентов</strong><span>Университетское событие без привязки к программе.</span>`}</div></div><section class="campus-context" data-testid="event-campus"><div class="section-heading"><div><p class="eyebrow">Campus API</p><h2>Точка и связанные события</h2></div><span class="count" data-testid="event-campus-status">Проверяем…</span></div><div data-testid="event-campus-content"><p class="muted">Загружаем карточку корпуса, чтобы показать актуальные связи.</p></div></section><p class="event-provenance">Источник: ${event.provenance.map((item) => `<a href="${safeHref(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.kind)}</a>`).join(" · ")}</p></article>`;
}

async function loadCampusContext(root: HTMLElement, event: Event): Promise<void> {
  const campusRoot = root.querySelector<HTMLElement>("[data-testid='event-campus-content']");
  const status = root.querySelector<HTMLElement>("[data-testid='event-campus-status']");
  const venueId = event.venue?.id;
  if (!campusRoot || !status || !venueId) {
    if (status) status.textContent = "Без точки";
    if (campusRoot) campusRoot.innerHTML = `<p class="muted">Для онлайн-события физическая точка не требуется.</p>`;
    return;
  }
  const [pointResult, eventsResult] = await Promise.allSettled([getCampusPoint(venueId), getCampusPointEvents(venueId, { limit: 5 })]);
  const point = pointResult.status === "fulfilled" ? pointResult.value : null;
  const related = eventsResult.status === "fulfilled" ? eventsResult.value : null;
  if (!point) {
    status.textContent = "Нет данных";
    campusRoot.innerHTML = `<p class="muted">Карточка campus point временно недоступна, но исходное место события сохранено выше.</p>`;
    return;
  }
  status.textContent = `${point.eventCount} событий`;
  campusRoot.innerHTML = renderCampusPoint(point, related);
}

function renderCampusPoint(point: CampusPointResponse, related: CampusPointEventsResponse | null): string {
  const programs = point.programs.slice(0, 3).map((program) => `<a href="#program/${encodeURIComponent(program.id)}">${escapeHtml(program.code)} · ${escapeHtml(program.name)}</a>`).join("");
  const events = related?.items.slice(0, 4).map((event) => `<li><a href="#event/${encodeURIComponent(event.id)}">${escapeHtml(event.title)}</a><time datetime="${escapeHtml(event.startsAt)}">${escapeHtml(formatDate(event.startsAt))}</time></li>`).join("") ?? "";
  return `<div class="campus-point-card"><div><span class="label">${escapeHtml(point.pointType)}</span><h3>${escapeHtml(point.name)}</h3>${point.address ? `<p>${escapeHtml(point.address)}</p>` : ""}${point.latitude !== null && point.latitude !== undefined && point.longitude !== null && point.longitude !== undefined ? `<small>Координаты: ${escapeHtml(point.latitude)}, ${escapeHtml(point.longitude)}</small>` : ""}</div>${programs ? `<div><span class="label">Связанные программы</span><div class="stacked-links">${programs}</div></div>` : ""}${events ? `<div><span class="label">Другие события здесь</span><ul class="campus-event-list">${events}</ul></div>` : ""}</div>`;
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : new Intl.DateTimeFormat("ru-RU", { dateStyle: "full", timeStyle: "short" }).format(date);
}

function safeHref(value: string): string {
  try {
    const url = new URL(value, window.location.origin);
    return url.protocol === "http:" || url.protocol === "https:" ? escapeHtml(url.href) : "#";
  } catch {
    return "#";
  }
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
