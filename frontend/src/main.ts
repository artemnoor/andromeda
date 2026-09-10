import { comparePrograms, getCurriculum, getProgram } from "./api/client";
import { ApiError } from "./api/errors";
import { renderCompareScreen } from "./features/compare/CompareScreen";
import { renderCurriculumScreen } from "./features/curriculum/CurriculumScreen";
import { renderProgramScreen } from "./features/program/ProgramScreen";
import "./styles.css";

const root = document.querySelector<HTMLElement>("#app");
if (!root) throw new Error("Application root is missing");
const appRoot: HTMLElement = root;

const programIds: readonly [string, string] = ["program:09.03.01-02", "program:09.03.01-12"];
const query = new URLSearchParams(window.location.search);
const singleProgramId = query.get("program");
const view = query.get("view");
appRoot.innerHTML = "<p class=\"loading\">Загружаем данные из API…</p>";

async function load(): Promise<void> {
  try {
    if (singleProgramId && view === "curriculum") {
      renderCurriculumScreen(appRoot, await getCurriculum(singleProgramId));
    } else if (singleProgramId) {
      renderProgramScreen(appRoot, await getProgram(singleProgramId));
    } else {
      renderCompareScreen(appRoot, await comparePrograms(programIds));
    }
  } catch (error: unknown) {
    const message = error instanceof ApiError ? `${error.payload.code}: ${error.payload.message}` : "Не удалось загрузить контрактный ответ API";
    appRoot.innerHTML = `<section class="error"><p class="eyebrow">Ошибка контракта</p><h1>${escapeHtml(message)}</h1><p>Проверьте, что backend запущен и база заполнена tracer-bullet командой.</p></section>`;
  }
}

void load();

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
