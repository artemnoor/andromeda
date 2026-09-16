import type { components } from "../../api/generated";

type Program = components["schemas"]["ProgramSummaryResponse"];
export type CatalogFilters = Readonly<{ search: string; year: string; direction: string }>;

export function filterCatalogPrograms(programs: readonly Program[], filters: CatalogFilters): readonly Program[] {
  const needle = filters.search.trim().toLocaleLowerCase("ru-RU");
  return programs.filter((program) => {
    const haystack = `${program.code} ${program.name} ${program.directionId}`.toLocaleLowerCase("ru-RU");
    return (!needle || haystack.includes(needle)) && (!filters.year || String(program.educationYear) === filters.year) && (!filters.direction || program.directionId === filters.direction);
  });
}

export function renderCatalogPage(root: HTMLElement, programs: readonly Program[]): void {
  root.innerHTML = `<section class="hero catalog-hero" data-testid="catalog-page"><div class="hero-kicker"><span class="eyebrow">Andromeda · каталог</span><span class="hero-index">01 / 10</span></div><h1>Найди программу, которая звучит твоими предметами.</h1><p class="lead">Смотри на реальные учебные планы МГТУ как на карту содержания — без рекламных обещаний и случайных рейтингов.</p><div class="hero-actions"><a class="primary-button" href="#proftest">Подобрать по интересам</a><a class="text-link" href="#compare">Сравнить две программы <span aria-hidden="true">→</span></a></div></section><section class="catalog-toolbar" aria-label="Фильтры каталога"><div class="catalog-search-field"><label for="catalog-search">Поиск по каталогу</label><input id="catalog-search" data-testid="catalog-search" type="search" placeholder="Например, информатика или робототехника" autocomplete="off"></div><label><span>Год учебного плана</span><select data-testid="catalog-year"><option value="">Все годы</option>${yearOptions(programs)}</select></label><label><span>Направление</span><select data-testid="catalog-direction"><option value="">Все направления</option>${directionOptions(programs)}</select></label><button class="secondary-button catalog-reset" data-testid="catalog-reset" type="button">Сбросить</button></section><section class="catalog-results" aria-live="polite"><div class="section-heading"><div><p class="eyebrow">Реальные программы</p><h2>Каталог</h2></div><span class="count" data-testid="catalog-result-count"></span></div><div class="catalog-grid" data-testid="catalog-grid"></div></section>`;

  const search = root.querySelector<HTMLInputElement>("[data-testid='catalog-search']");
  const year = root.querySelector<HTMLSelectElement>("[data-testid='catalog-year']");
  const direction = root.querySelector<HTMLSelectElement>("[data-testid='catalog-direction']");
  const reset = root.querySelector<HTMLButtonElement>("[data-testid='catalog-reset']");
  const count = root.querySelector<HTMLElement>("[data-testid='catalog-result-count']");
  const grid = root.querySelector<HTMLElement>("[data-testid='catalog-grid']");
  if (!search || !year || !direction || !reset || !count || !grid) return;

  const renderResults = (): void => {
    const visible = filterCatalogPrograms(programs, { search: search.value, year: year.value, direction: direction.value });
    count.textContent = `${visible.length} ${pluralize(visible.length, "программа", "программы", "программ")}`;
    grid.innerHTML = visible.length > 0 ? visible.map(renderProgramCard).join("") : `<div class="empty-state catalog-empty" data-testid="catalog-empty"><p class="eyebrow">Ничего не найдено</p><h3>Попробуй изменить запрос</h3><p>Каталог ищет по коду, названию и направлению программы.</p></div>`;
  };

  search.addEventListener("input", renderResults);
  year.addEventListener("change", renderResults);
  direction.addEventListener("change", renderResults);
  reset.addEventListener("click", () => {
    search.value = "";
    year.value = "";
    direction.value = "";
    renderResults();
    search.focus();
  });
  renderResults();
}

function renderProgramCard(program: Program): string {
  return `<article class="catalog-card" data-testid="catalog-program-card"><div class="catalog-card-topline"><span class="status">${escapeHtml(program.code)}</span><span class="catalog-year">${program.educationYear}</span></div><h3>${escapeHtml(program.name)}</h3><p>${escapeHtml(program.directionId)}</p><div class="catalog-card-actions"><a class="primary-button" data-testid="catalog-program-link" href="#program/${encodeURIComponent(program.id)}">Открыть программу</a><a class="text-link" href="#compare">Сравнить <span aria-hidden="true">→</span></a></div></article>`;
}

function yearOptions(programs: readonly Program[]): string {
  return [...new Set(programs.map((program) => program.educationYear))].sort((a, b) => b - a).map((value) => `<option value="${value}">${value}</option>`).join("");
}

function directionOptions(programs: readonly Program[]): string {
  return [...new Set(programs.map((program) => program.directionId))].sort().map((value) => `<option value="${escapeAttribute(value)}">${escapeHtml(value)}</option>`).join("");
}

function pluralize(value: number, one: string, few: string, many: string): string {
  const mod10 = value % 10;
  const mod100 = value % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return few;
  return many;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}

function escapeAttribute(value: string): string {
  return escapeHtml(value);
}
