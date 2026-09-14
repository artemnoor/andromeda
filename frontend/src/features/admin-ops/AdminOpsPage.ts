import { ApiError } from "../../api/errors";
import {
  getIngestionRun,
  getIngestionRuns,
  retryIngestion,
  type IngestionRetryRequest,
  type IngestionRunDetailResponse,
  type IngestionRunListResponse,
  type IngestionRunStatus,
} from "../../api/client";

type IngestionRunSummary = IngestionRunListResponse["items"][number];

const statusLabels: Record<IngestionRunStatus, string> = {
  running: "Выполняется",
  completed: "Завершён",
  failed: "Ошибка",
};

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : date.toLocaleString("ru-RU");
}

function safeErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) return "Доступ к операторскому API не предоставлен.";
    return error.payload.message;
  }
  return "Операторский API временно недоступен.";
}

function summaryHtml(run: IngestionRunSummary): string {
  return [
    '<button class="ops-run-row" data-testid="ops-run-row" data-run-id="',
    escapeHtml(run.id),
    '" type="button">',
    '<span><strong>',
    escapeHtml(run.id),
    '</strong><small>',
    escapeHtml(formatDate(run.startedAt)),
    "</small></span>",
    '<span class="status">',
    escapeHtml(statusLabels[run.status]),
    "</span>",
    "<span>",
    escapeHtml(run.sourceCount + " источн. · " + run.programCount + " программ · " + run.eventCount + " событий"),
    "</span>",
    "</button>",
  ].join("");
}

function metricHtml(label: string, value: number): string {
  return '<div class="ops-metric"><strong>' + escapeHtml(String(value)) + "</strong><span>" + escapeHtml(label) + "</span></div>";
}

export function renderAdminOpsPage(root: HTMLElement): void {
  root.innerHTML = [
    '<section class="ops-shell" data-testid="ops-page">',
    '<div class="ops-hero"><p class="eyebrow">Operator access · protected</p><h1>Контроль ingestion</h1><p class="lead">Служебный просмотр аудита и ограниченный повтор BMSTU fixture. Сырые payload и тела источников здесь недоступны.</p></div>',
    '<form class="ops-key-form" data-testid="ops-key-form"><label for="ops-key">Ops API key</label><input id="ops-key" data-testid="ops-key" type="password" autocomplete="off" required><button class="primary-button" data-testid="ops-connect" type="submit">Подключиться</button></form>',
    '<p class="ops-form-error" data-testid="ops-form-error" hidden></p>',
    '<div class="ops-workspace" data-testid="ops-workspace" hidden>',
    '<div class="ops-toolbar"><label for="ops-status-filter">Статус<select id="ops-status-filter" data-testid="ops-status-filter"><option value="">Все</option><option value="running">Выполняется</option><option value="completed">Завершён</option><option value="failed">Ошибка</option></select></label><button class="secondary-button" data-testid="ops-refresh" type="button">Обновить</button></div>',
    '<div class="ops-layout"><section><div class="section-heading"><h2>Запуски</h2><span class="count" data-testid="ops-count"></span></div><div data-testid="ops-list"></div></section><aside data-testid="ops-detail"></aside></div>',
    "</div></section>",
  ].join("");

  const keyForm = root.querySelector<HTMLFormElement>("[data-testid='ops-key-form']");
  const keyInput = root.querySelector<HTMLInputElement>("[data-testid='ops-key']");
  const formError = root.querySelector<HTMLElement>("[data-testid='ops-form-error']");
  const workspace = root.querySelector<HTMLElement>("[data-testid='ops-workspace']");
  const list = root.querySelector<HTMLElement>("[data-testid='ops-list']");
  const detail = root.querySelector<HTMLElement>("[data-testid='ops-detail']");
  const filter = root.querySelector<HTMLSelectElement>("[data-testid='ops-status-filter']");
  const count = root.querySelector<HTMLElement>("[data-testid='ops-count']");
  const refresh = root.querySelector<HTMLButtonElement>("[data-testid='ops-refresh']");
  if (!keyForm || !keyInput || !formError || !workspace || !list || !detail || !filter || !count || !refresh) return;

  let opsKey = "";
  let selectedRunId: string | undefined;
  let loading = false;

  const renderList = (runs: readonly IngestionRunSummary[]): void => {
    count.textContent = String(runs.length);
    if (runs.length === 0) {
      list.innerHTML = '<p class="empty-state" data-testid="ops-empty">Запусков с выбранным статусом пока нет.</p>';
      return;
    }
    list.innerHTML = runs.map(summaryHtml).join("");
    list.querySelectorAll<HTMLButtonElement>("[data-run-id]").forEach((button) => {
      button.addEventListener("click", () => {
        selectedRunId = button.dataset.runId;
        void loadDetail();
      });
    });
  };

  const renderDetail = (run: IngestionRunDetailResponse["run"]): void => {
    const errorBlock = run.status === "failed"
      ? '<div class="ops-error" data-testid="ops-error"><strong>' + escapeHtml(run.errorCode ?? "INGESTION_FAILED") + "</strong><p>" + escapeHtml(run.errorMessage ?? "Ingestion failed") + "</p></div>"
      : "";
    detail.innerHTML = [
      '<article class="detail-card ops-detail-card"><div class="detail-heading"><div><p class="eyebrow">Audit detail</p><h2>',
      escapeHtml(run.id),
      '</h2></div><span class="status">',
      escapeHtml(statusLabels[run.status]),
      "</span></div>",
      '<p class="muted">Начат: ',
      escapeHtml(formatDate(run.startedAt)),
      " · завершён: ",
      escapeHtml(formatDate(run.finishedAt)),
      "</p>",
      '<div class="ops-metrics">',
      metricHtml("Источники", run.sourceCount),
      metricHtml("Программы", run.programCount),
      metricHtml("Учебные элементы", run.curriculumItemCount),
      metricHtml("События", run.eventCount),
      metricHtml("Корпуса/точки", run.campusPointCount),
      metricHtml("Добавлено", run.insertedCount),
      metricHtml("Обновлено", run.updatedCount),
      metricHtml("Без изменений", run.unchangedCount),
      metricHtml("Удалено", run.removedCount),
      "</div>",
      errorBlock,
      '<div class="ops-detail-grid"><section><h3>Источники</h3><ul class="compact-list">',
      run.sourceKinds.map((kind, index) => "<li><span>" + escapeHtml(kind) + "</span><code>" + escapeHtml(run.sourceHashes[index] ?? "hash unavailable") + "</code></li>").join(""),
      "</ul></section><section><h3>Доступность данных</h3><p class=\"muted\">Конфликты и неразобранные записи текущий ingestion contract не сохраняет; значение не подменяется нулём.</p></section></div>",
      '<button class="primary-button" data-testid="ops-retry" type="button">Повторить BMSTU fixture</button>',
      "</article>",
    ].join("");
    const retry = detail.querySelector<HTMLButtonElement>("[data-testid='ops-retry']");
    retry?.addEventListener("click", () => {
      if (window.confirm("Запустить новый ingestion BMSTU fixture?")) void runRetry(retry);
    });
  };

  const loadDetail = async (): Promise<void> => {
    if (!selectedRunId || !opsKey) return;
    detail.innerHTML = '<p class="loading" data-testid="ops-loading">Загружаем detail…</p>';
    try {
      const response = await getIngestionRun(selectedRunId, opsKey);
      renderDetail(response.run);
    } catch (error: unknown) {
      detail.innerHTML = '<p class="error" data-testid="ops-error-state">' + escapeHtml(safeErrorMessage(error)) + "</p>";
    }
  };

  const loadRuns = async (): Promise<void> => {
    if (!opsKey) return;
    loading = true;
    refresh.disabled = true;
    list.innerHTML = '<p class="loading" data-testid="ops-loading">Загружаем запуски…</p>';
    try {
      const status = filter.value as IngestionRunStatus | "";
      const response = await getIngestionRuns(status ? { status, limit: 100 } : { limit: 100 }, opsKey);
      renderList(response.items);
      if (response.items.length === 0) {
        detail.innerHTML = "";
      } else if (!selectedRunId || !response.items.some((run) => run.id === selectedRunId)) {
        selectedRunId = response.items[0]?.id;
        await loadDetail();
      } else {
        await loadDetail();
      }
    } catch (error: unknown) {
      count.textContent = "";
      list.innerHTML = '<p class="error" data-testid="ops-error-state">' + escapeHtml(safeErrorMessage(error)) + "</p>";
      detail.innerHTML = "";
    } finally {
      loading = false;
      refresh.disabled = false;
    }
  };

  const runRetry = async (button: HTMLButtonElement): Promise<void> => {
    if (loading || !opsKey) return;
    loading = true;
    button.disabled = true;
    try {
      const request: IngestionRetryRequest = { source: "bmstu_fixture" };
      const response = await retryIngestion(request, opsKey);
      selectedRunId = response.run.id;
      await loadRuns();
    } catch (error: unknown) {
      detail.innerHTML = '<p class="error" data-testid="ops-error-state">' + escapeHtml(safeErrorMessage(error)) + "</p>";
    } finally {
      loading = false;
      button.disabled = false;
    }
  };

  keyForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const value = keyInput.value.trim();
    keyInput.value = "";
    if (!value) {
      formError.hidden = false;
      formError.textContent = "Введите Ops API key.";
      return;
    }
    opsKey = value;
    formError.hidden = true;
    workspace.hidden = false;
    void loadRuns();
  });
  filter.addEventListener("change", () => void loadRuns());
  refresh.addEventListener("click", () => void loadRuns());
}
