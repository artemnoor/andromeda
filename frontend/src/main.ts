import { getPrograms } from "./api/client";
import { ApiError } from "./api/errors";
import { renderAppShell } from "./features/AppShell";
import "./styles.css";

const root = document.querySelector<HTMLElement>("#app");
if (!root) throw new Error("Application root is missing");
const appRoot: HTMLElement = root;

appRoot.innerHTML = "<p class=\"loading\">Загружаем данные из API…</p>";

async function load(): Promise<void> {
  try {
    const response = await getPrograms();
    renderAppShell(appRoot, response.items);
  } catch (error: unknown) {
    const message = error instanceof ApiError ? `${error.payload.code}: ${error.payload.message}` : "Не удалось загрузить контрактный ответ API";
    appRoot.innerHTML = `<section class="error"><p class="eyebrow">Ошибка контракта</p><h1>${escapeHtml(message)}</h1><p>Проверьте, что backend запущен и база заполнена tracer-bullet командой.</p></section>`;
  }
}

void load();

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
