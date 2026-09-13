function state(root: HTMLElement, className: string, testId: string, eyebrow: string, heading: string, body: string): void {
  const role = className === "personal-route-error" ? "alert" : "status";
  root.innerHTML = `<section class="state-card personal-route-state ${escapeHtml(className)}" data-testid="${escapeHtml(testId)}" role="${role}"><p class="eyebrow">${escapeHtml(eyebrow)}</p><h2>${escapeHtml(heading)}</h2><p>${escapeHtml(body)}</p></section>`;
}

export function renderPersonalRouteLoading(root: HTMLElement): void {
  state(root, "personal-route-loading", "personal-route-loading", "Мой план", "Собираем персональный план", "Сверяем рекомендации, события и связанные места университета.");
}

export function renderPersonalRouteError(root: HTMLElement, message: string): void {
  state(root, "personal-route-error", "personal-route-error", "Ошибка API", message, "Проверьте соединение с backend и повторите запрос.");
}

export function renderPersonalRouteProfileRequired(root: HTMLElement): void {
  root.innerHTML = `<section class="state-card personal-route-state personal-route-profile-required" data-testid="personal-route-profile-required"><p class="eyebrow">Персональный план</p><h2>Сначала пройдите профтест</h2><p>План строится по сохранённым рекомендациям профиля содержания.</p><a class="primary-button" data-testid="personal-route-profile-link" href="#proftest">Открыть профтест</a></section>`;
}

export function renderPersonalRouteNoRecommendations(root: HTMLElement): void {
  root.innerHTML = `<section class="state-card personal-route-state personal-route-empty" data-testid="personal-route-empty"><p class="eyebrow">Персональный план</p><h2>Пока не из чего собрать план</h2><p>Пройдите профтест ещё раз или обновите профиль, чтобы получить рекомендации по программам.</p><a class="primary-button" data-testid="personal-route-profile-link" href="#proftest">Открыть профтест</a></section>`;
}

export function renderPersonalRouteNoEvents(root: HTMLElement): void {
  root.innerHTML = personalRouteNoEventsMarkup();
}

export function personalRouteNoEventsMarkup(): string {
  return `<section class="state-card personal-route-state personal-route-no-events" data-testid="personal-route-no-events" role="status"><p class="eyebrow">Персональный план</p><h3>Рекомендации готовы, событий пока нет</h3><p>Программы уже доступны ниже. Новые мероприятия появятся, когда в каталоге будут подходящие будущие события.</p></section>`;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
