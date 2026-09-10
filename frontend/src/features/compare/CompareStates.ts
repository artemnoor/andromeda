export function renderLoading(root: HTMLElement): void {
  root.innerHTML = `<p class="loading" data-testid="comparison-loading" role="status">Считаем сравнение…</p>`;
}

export function renderEmpty(root: HTMLElement, message: string): void {
  root.innerHTML = `<section class="empty-state"><p class="eyebrow">Нет данных</p><h2>${escapeHtml(message)}</h2><p>Выберите две программы с опубликованными учебными планами.</p></section>`;
}

export function renderError(root: HTMLElement, message: string): void {
  root.innerHTML = `<section class="error" role="alert"><p class="eyebrow">Ошибка API</p><h2>${escapeHtml(message)}</h2><p>Проверьте, что backend запущен и база заполнена.</p></section>`;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
