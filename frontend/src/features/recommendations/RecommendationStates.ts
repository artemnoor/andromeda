import { ApiError, ApiTimeoutError } from "../../api/errors";
import { escapeHtml } from "../proftest/rendering";

export function renderRecommendationLoading(root: HTMLElement): void {
  root.innerHTML = `<section class="state-card" data-testid="proftest-loading" role="status" aria-live="polite"><p class="eyebrow">Andromeda · рекомендации</p><h2>Собираем персональный TOP программ…</h2><p>Сопоставляем профиль с реальными учебными планами и объясняем каждое совпадение.</p><p class="muted">Полный каталог обрабатывается несколько секунд. Если ответ не появится, запрос можно будет повторить.</p><a class="secondary-button" data-testid="proftest-loading-catalog" href="#catalog">Вернуться в каталог</a></section>`;
}

export function renderRecommendationEmpty(root: HTMLElement, message: string): void {
  root.innerHTML = `<section class="state-card" data-testid="proftest-empty"><p class="eyebrow">Нет данных</p><h2>${escapeHtml(message)}</h2><p>Попробуйте изменить ответы или дождитесь расширения каталога программ.</p></section>`;
}

export function renderRecommendationError(root: HTMLElement, error: unknown, onRetry?: () => void): void {
  const message = error instanceof ApiError ? `${error.payload.code}: ${error.payload.message}` : error instanceof ApiTimeoutError ? "Каталог не ответил вовремя" : "Не удалось получить рекомендации";
  const details = error instanceof ApiTimeoutError ? "Расчёт полного каталога занял слишком много времени. Повторите запрос или продолжите как гость в каталоге." : "Проверьте, что backend запущен и в базе есть реальные учебные планы.";
  const retry = onRetry ? `<button class="primary-button" data-testid="proftest-retry" type="button">Повторить расчёт</button>` : "";
  root.innerHTML = `<section class="state-card error" data-testid="proftest-error" role="alert"><p class="eyebrow">Ошибка API</p><h2>${escapeHtml(message)}</h2><p>${escapeHtml(details)}</p><div class="hero-actions">${retry}<a class="secondary-button" href="#catalog">Открыть каталог</a></div></section>`;
  root.querySelector<HTMLButtonElement>("[data-testid='proftest-retry']")?.addEventListener("click", () => onRetry?.());
}

export function renderAdaptiveSkipped(root: HTMLElement, reason: string | null): void {
  root.innerHTML = `<section class="state-card adaptive-skipped" data-testid="adaptive-skipped"><p class="eyebrow">Уточнение не требуется</p><h2>Кандидаты уже достаточно похожи</h2><p>${escapeHtml(reason ?? "Для текущего каталога дополнительный вопрос не даст полезного различия.")}</p><button class="primary-button" data-testid="adaptive-skipped-continue" type="button">Показать программы</button></section>`;
}
