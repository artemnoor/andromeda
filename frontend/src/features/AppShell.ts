import type { components } from "../api/generated";
import { renderComparePage } from "./compare/ComparePage";
import { renderProftestPage } from "./proftest/ProftestPage";
import { renderProgramPage } from "./program/ProgramPage";
import { renderEventsPage } from "./events/EventsPage";
import { renderPersonalRoutePage } from "./personal-route/PersonalRoutePage";
import { renderUnifiedMvpPage } from "./unified-flow/UnifiedMvpPage";
import { renderAdminOpsPage } from "./admin-ops/AdminOpsPage";
import { renderAuthPanel } from "./auth/AuthPanel";

type Program = components["schemas"]["ProgramSummaryResponse"];

export type Feature = "flow" | "compare" | "events" | "personal-route" | "proftest" | "program" | "ops";

export type FeatureSelection = Readonly<{ feature: Feature; programId?: string }>;

export function parseFeatureHash(hash: string): FeatureSelection {
  if (hash === "#flow") return { feature: "flow" };
  if (hash === "#program") return { feature: "program" };
  if (hash.startsWith("#program/")) return { feature: "program", programId: decodeURIComponent(hash.slice("#program/".length)) };
  if (hash === "#events") return { feature: "events" };
  if (hash === "#personal-route") return { feature: "personal-route" };
  if (hash === "#proftest") return { feature: "proftest" };
  if (hash === "#ops") return { feature: "ops" };
  return { feature: "compare" };
}
export function hashForFeature(feature: Feature, firstProgramId?: string): string {
  return feature === "program" && firstProgramId ? `#program/${encodeURIComponent(firstProgramId)}` : `#${feature}`;
}

export function renderAppShell(root: HTMLElement, programs: readonly Program[]): void {
  root.innerHTML = `<header class="app-nav"><div><p class="eyebrow">Andromeda · BMSTU</p><strong class="app-brand">Учебные планы как данные</strong></div><nav aria-label="Разделы приложения"><button class="nav-button" data-testid="nav-unified-flow" type="button">Единый путь</button><button class="nav-button active" data-testid="nav-compare" type="button">Сравнение</button><button class="nav-button" data-testid="nav-events" type="button">События</button><button class="nav-button" data-testid="nav-personal-route" type="button">Мой план</button><button class="nav-button" data-testid="nav-proftest" type="button">Профиль содержания</button><button class="nav-button" data-testid="nav-program" type="button">Программа</button></nav></header><div id="auth-root"></div><div id="feature-root"></div>`;
  const authRoot = root.querySelector<HTMLElement>("#auth-root");
  const featureRoot = root.querySelector<HTMLElement>("#feature-root");
  const flowButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-unified-flow']");
  const compareButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-compare']");
  const eventsButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-events']");
  const personalRouteButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-personal-route']");
  const proftestButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-proftest']");
  const programButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-program']");
  if (!authRoot || !featureRoot || !flowButton || !compareButton || !eventsButton || !personalRouteButton || !proftestButton || !programButton) return;
  renderAuthPanel(authRoot);

  const select = (feature: Feature, programId?: string): void => {
    flowButton.classList.toggle("active", feature === "flow");
    compareButton.classList.toggle("active", feature === "compare");
    eventsButton.classList.toggle("active", feature === "events");
    personalRouteButton.classList.toggle("active", feature === "personal-route");
    proftestButton.classList.toggle("active", feature === "proftest");
    programButton.classList.toggle("active", feature === "program");
    if (feature === "flow") renderUnifiedMvpPage(featureRoot, programs);
    else if (feature === "compare") renderComparePage(featureRoot, programs);
    else if (feature === "events") renderEventsPage(featureRoot, programs);
    else if (feature === "personal-route") renderPersonalRoutePage(featureRoot, programs);
    else if (feature === "proftest") renderProftestPage(featureRoot);
    else if (feature === "ops") renderAdminOpsPage(featureRoot);
    else renderProgramPage(featureRoot, programs, programId);
  };
  const navigate = (feature: Feature): void => {
    const hash = hashForFeature(feature, programs[0]?.id);
    if (window.location.hash !== hash) window.location.hash = hash;
    else select(feature, programs[0]?.id);
  };
  const featureFromHash = (): FeatureSelection => parseFeatureHash(window.location.hash);
  flowButton.addEventListener("click", () => navigate("flow"));
  compareButton.addEventListener("click", () => navigate("compare"));
  eventsButton.addEventListener("click", () => navigate("events"));
  personalRouteButton.addEventListener("click", () => navigate("personal-route"));
  proftestButton.addEventListener("click", () => navigate("proftest"));
  programButton.addEventListener("click", () => navigate("program"));
  window.addEventListener("hashchange", () => {
    const { feature, programId } = featureFromHash();
    select(feature, programId);
  });
  const initial = featureFromHash();
  select(initial.feature, initial.programId);
}
