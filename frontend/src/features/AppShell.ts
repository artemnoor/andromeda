import type { components } from "../api/generated";
import { renderComparePage } from "./compare/ComparePage";
import { renderProftestPage } from "./proftest/ProftestPage";
import { renderProgramPage } from "./program/ProgramPage";
import { renderEventsPage } from "./events/EventsPage";

type Program = components["schemas"]["ProgramSummaryResponse"];

export function renderAppShell(root: HTMLElement, programs: readonly Program[]): void {
  root.innerHTML = `<header class="app-nav"><div><p class="eyebrow">Andromeda · BMSTU</p><strong class="app-brand">Учебные планы как данные</strong></div><nav aria-label="Разделы приложения"><button class="nav-button active" data-testid="nav-compare" type="button">Сравнение</button><button class="nav-button" data-testid="nav-events" type="button">События</button><button class="nav-button" data-testid="nav-proftest" type="button">Профиль содержания</button><button class="nav-button" data-testid="nav-program" type="button">Программа</button></nav></header><div id="feature-root"></div>`;
  const featureRoot = root.querySelector<HTMLElement>("#feature-root");
  const compareButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-compare']");
  const eventsButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-events']");
  const proftestButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-proftest']");
  const programButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-program']");
  if (!featureRoot || !compareButton || !eventsButton || !proftestButton || !programButton) return;

  type Feature = "compare" | "events" | "proftest" | "program";
  const select = (feature: Feature, programId?: string): void => {
    compareButton.classList.toggle("active", feature === "compare");
    eventsButton.classList.toggle("active", feature === "events");
    proftestButton.classList.toggle("active", feature === "proftest");
    programButton.classList.toggle("active", feature === "program");
    if (feature === "compare") renderComparePage(featureRoot, programs);
    else if (feature === "events") renderEventsPage(featureRoot, programs);
    else if (feature === "proftest") renderProftestPage(featureRoot);
    else renderProgramPage(featureRoot, programs, programId);
  };
  const navigate = (feature: Feature): void => {
    const firstProgramId = programs[0]?.id;
    const hash = feature === "program" && firstProgramId ? `#program/${encodeURIComponent(firstProgramId)}` : `#${feature}`;
    if (window.location.hash !== hash) window.location.hash = hash;
    else select(feature, firstProgramId);
  };
  const featureFromHash = (): { feature: Feature; programId?: string } => {
    if (window.location.hash === "#program") return { feature: "program" };
    if (window.location.hash.startsWith("#program/")) return { feature: "program", programId: decodeURIComponent(window.location.hash.slice("#program/".length)) };
    if (window.location.hash === "#events") return { feature: "events" };
    if (window.location.hash === "#proftest") return { feature: "proftest" };
    return { feature: "compare" };
  };
  compareButton.addEventListener("click", () => navigate("compare"));
  eventsButton.addEventListener("click", () => navigate("events"));
  proftestButton.addEventListener("click", () => navigate("proftest"));
  programButton.addEventListener("click", () => navigate("program"));
  window.addEventListener("hashchange", () => {
    const { feature, programId } = featureFromHash();
    select(feature, programId);
  });
  const initial = featureFromHash();
  select(initial.feature, initial.programId);
}
