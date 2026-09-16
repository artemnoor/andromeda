import type { components } from "../api/generated";
import { renderComparePage } from "./compare/ComparePage";
import { renderProftestPage } from "./proftest/ProftestPage";
import { renderProgramPage } from "./program/ProgramPage";
import { renderEventsPage } from "./events/EventsPage";
import { renderPersonalRoutePage } from "./personal-route/PersonalRoutePage";
import { renderUnifiedMvpPage } from "./unified-flow/UnifiedMvpPage";
import { renderAdminOpsPage } from "./admin-ops/AdminOpsPage";
import { renderAuthPanel } from "./auth/AuthPanel";
import { renderCatalogPage } from "./catalog/CatalogPage";
import { renderRecommendationsPage } from "./recommendations/RecommendationsPage";
import { renderAccountPage } from "./account/AccountPage";
import { renderEventPage } from "./events/EventPage";

type Program = components["schemas"]["ProgramSummaryResponse"];

export type Feature = "catalog" | "flow" | "compare" | "events" | "event" | "personal-route" | "proftest" | "recommendations" | "program" | "account" | "ops";

export type FeatureSelection = Readonly<{ feature: Feature; programId?: string; eventId?: string }>;

export function parseFeatureHash(hash: string): FeatureSelection {
  if (hash === "#catalog") return { feature: "catalog" };
  if (hash === "#flow") return { feature: "flow" };
  if (hash === "#program") return { feature: "program" };
  if (hash.startsWith("#program/")) return { feature: "program", programId: decodeURIComponent(hash.slice("#program/".length)) };
  if (hash === "#events") return { feature: "events" };
  if (hash.startsWith("#event/")) return { feature: "event", eventId: decodeURIComponent(hash.slice("#event/".length)) };
  if (hash === "#personal-route") return { feature: "personal-route" };
  if (hash === "#proftest") return { feature: "proftest" };
  if (hash === "#recommendations") return { feature: "recommendations" };
  if (hash === "#account") return { feature: "account" };
  if (hash === "#ops") return { feature: "ops" };
  return { feature: "compare" };
}
export function hashForFeature(feature: Feature, firstProgramId?: string): string {
  if (feature === "program" && firstProgramId) return `#program/${encodeURIComponent(firstProgramId)}`;
  return `#${feature}`;
}

export function renderAppShell(root: HTMLElement, programs: readonly Program[]): void {
  root.innerHTML = `<a class="skip-link" href="#feature-root">К содержанию</a><header class="app-nav"><a class="app-brand-block" href="#catalog" aria-label="Andromeda, перейти в каталог"><span class="brand-mark" aria-hidden="true">A</span><span><span class="eyebrow">Andromeda · BMSTU</span><strong class="app-brand">Учебные планы как данные</strong></span></a><nav class="app-nav-primary" aria-label="Основные разделы"><button class="nav-button" data-testid="nav-catalog" type="button">Каталог</button><button class="nav-button" data-testid="nav-compare" type="button">Сравнить</button><button class="nav-button" data-testid="nav-proftest" type="button">Профиль</button><button class="nav-button" data-testid="nav-recommendations" type="button">Рекомендации</button><button class="nav-button" data-testid="nav-events" type="button">События</button><button class="nav-button" data-testid="nav-personal-route" type="button">Мой план</button></nav><nav class="app-nav-utility" aria-label="Дополнительные разделы"><button class="nav-button nav-button-flow" data-testid="nav-unified-flow" type="button">Путь</button><button class="nav-button" data-testid="nav-program" type="button">Программа</button></nav><div id="auth-root" class="app-nav-profile"></div></header><div class="shell-note"><span>Source-backed data · BMSTU</span><span>Обновляем только через API</span></div><div id="feature-root" tabindex="-1"></div>`;
  const authRoot = root.querySelector<HTMLElement>("#auth-root");
  const featureRoot = root.querySelector<HTMLElement>("#feature-root");
  const catalogButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-catalog']");
  const flowButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-unified-flow']");
  const compareButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-compare']");
  const recommendationsButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-recommendations']");
  const eventsButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-events']");
  const personalRouteButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-personal-route']");
  const proftestButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-proftest']");
  const programButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-program']");
  if (!authRoot || !featureRoot || !catalogButton || !flowButton || !compareButton || !recommendationsButton || !eventsButton || !personalRouteButton || !proftestButton || !programButton) return;

  const buttons: ReadonlyArray<[Feature, HTMLButtonElement]> = [["catalog", catalogButton], ["flow", flowButton], ["compare", compareButton], ["recommendations", recommendationsButton], ["events", eventsButton], ["personal-route", personalRouteButton], ["proftest", proftestButton], ["program", programButton]];
  const select = (feature: Feature, programId?: string, eventId?: string): void => {
    buttons.forEach(([buttonFeature, button]) => {
      const active = feature === buttonFeature || (feature === "event" && buttonFeature === "events");
      button.classList.toggle("active", active);
      if (active) button.setAttribute("aria-current", "page");
      else button.removeAttribute("aria-current");
    });
    if (feature === "catalog") renderCatalogPage(featureRoot, programs);
    else if (feature === "flow") renderUnifiedMvpPage(featureRoot, programs);
    else if (feature === "compare") renderComparePage(featureRoot, programs);
    else if (feature === "events") renderEventsPage(featureRoot, programs);
    else if (feature === "event" && eventId) renderEventPage(featureRoot, eventId, programs);
    else if (feature === "personal-route") renderPersonalRoutePage(featureRoot, programs);
    else if (feature === "proftest") renderProftestPage(featureRoot);
    else if (feature === "recommendations") renderRecommendationsPage(featureRoot);
    else if (feature === "account") renderAccountPage(featureRoot);
    else if (feature === "ops") renderAdminOpsPage(featureRoot);
    else renderProgramPage(featureRoot, programs, programId);
    featureRoot.focus({ preventScroll: true });
  };
  const navigate = (feature: Feature, id?: string): void => {
    const hash = feature === "event" && id ? `#event/${encodeURIComponent(id)}` : hashForFeature(feature, feature === "program" ? id ?? programs[0]?.id : undefined);
    if (window.location.hash !== hash) window.location.hash = hash;
    else select(feature, feature === "program" ? id ?? programs[0]?.id : undefined, feature === "event" ? id : undefined);
  };
  const featureFromHash = (): FeatureSelection => parseFeatureHash(window.location.hash);
  catalogButton.addEventListener("click", () => navigate("catalog"));
  flowButton.addEventListener("click", () => navigate("flow"));
  compareButton.addEventListener("click", () => navigate("compare"));
  recommendationsButton.addEventListener("click", () => navigate("recommendations"));
  eventsButton.addEventListener("click", () => navigate("events"));
  personalRouteButton.addEventListener("click", () => navigate("personal-route"));
  proftestButton.addEventListener("click", () => navigate("proftest"));
  programButton.addEventListener("click", () => navigate("program"));
  renderAuthPanel(authRoot, {
    onSessionChanged: (session) => {
      if (!session.authenticated && parseFeatureHash(window.location.hash).feature === "account") select("account");
    },
    onNavigateToAccount: () => navigate("account"),
  });
  window.addEventListener("hashchange", () => {
    const { feature, programId, eventId } = featureFromHash();
    select(feature, programId, eventId);
  });
  const initial = window.location.hash ? featureFromHash() : { feature: "catalog" as const };
  select(initial.feature, initial.programId, initial.eventId);
}
