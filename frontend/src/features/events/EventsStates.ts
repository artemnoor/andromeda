function state(root: HTMLElement, className: string, testId: string, eyebrow: string, heading: string, body: string): void {
  const role = className === "events-error" ? "alert" : "status";
  root.innerHTML = `<section class="state-card events-state ${escapeHtml(className)}" data-testid="${escapeHtml(testId)}" role="${role}"><p class="eyebrow">${escapeHtml(eyebrow)}</p><h2>${escapeHtml(heading)}</h2><p>${escapeHtml(body)}</p></section>`;
}

export function renderEventsLoading(root: HTMLElement): void {
  state(root, "events-loading", "events-loading", "События", "Загружаем мероприятия", "Проверяем актуальные даты и ссылки регистрации.");
}

export function renderEventsEmpty(root: HTMLElement, recommended: boolean): void {
  state(root, "events-empty", "events-empty", "События", recommended ? "Подходящих событий пока нет" : "Событий не найдено", recommended ? "Попробуйте позже или измените фильтры рекомендаций." : "Измените фильтры и попробуйте снова.");
}

export function renderEventsError(root: HTMLElement, message: string): void {
  try {
    state(root, "events-error", "events-error", "Ошибка API", message, "Проверьте соединение с backend и повторите запрос.");
    if (import.meta.env.DEV && import.meta.env.VITE_LOG_LEVEL === "DEBUG") {
      console.debug("[FIX:events-security] rendered escaped event API error", { messageLength: message.length });
    }
  } catch (error: unknown) {
    if (import.meta.env.DEV && import.meta.env.VITE_LOG_LEVEL === "DEBUG") {
      console.error("[FIX:events-security] failed to render event API error", { messageLength: message.length, error });
    }
    throw error;
  }
}

export function renderEventsProfileRequired(root: HTMLElement): void {
  root.innerHTML = `<section class="state-card events-state events-profile-required" data-testid="events-profile-required"><p class="eyebrow">Персональная подборка</p><h2>Сначала пройдите профтест</h2><p>Рекомендованные события появятся после сохранения профиля интересов.</p><a class="primary-button" data-testid="events-profile-link" href="#proftest">Открыть профтест</a></section>`;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
