import type { components } from "../api/generated";
import { renderComparePage } from "./compare/ComparePage";
import { renderProftestPage } from "./proftest/ProftestPage";

type Program = components["schemas"]["ProgramSummaryResponse"];

export function renderAppShell(root: HTMLElement, programs: readonly Program[]): void {
  root.innerHTML = `<header class="app-nav"><div><p class="eyebrow">Andromeda · BMSTU</p><strong class="app-brand">Учебные планы как данные</strong></div><nav aria-label="Разделы приложения"><button class="nav-button active" data-testid="nav-compare" type="button">Сравнение</button><button class="nav-button" data-testid="nav-proftest" type="button">Профиль содержания</button></nav></header><div id="feature-root"></div>`;
  const featureRoot = root.querySelector<HTMLElement>("#feature-root");
  const compareButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-compare']");
  const proftestButton = root.querySelector<HTMLButtonElement>("[data-testid='nav-proftest']");
  if (!featureRoot || !compareButton || !proftestButton) return;

  let selectedFeature: "compare" | "proftest" = "compare";
  const select = (feature: "compare" | "proftest"): void => {
    selectedFeature = feature;
    compareButton.classList.toggle("active", feature === "compare");
    proftestButton.classList.toggle("active", feature === "proftest");
    if (feature === "compare") renderComparePage(featureRoot, programs);
    else renderProftestPage(featureRoot);
  };
  const navigate = (feature: "compare" | "proftest"): void => {
    const hash = `#${feature}`;
    if (window.location.hash !== hash) window.location.hash = hash;
    select(feature);
  };
  const featureFromHash = (): "compare" | "proftest" => window.location.hash === "#proftest" ? "proftest" : "compare";
  compareButton.addEventListener("click", () => navigate("compare"));
  proftestButton.addEventListener("click", () => navigate("proftest"));
  window.addEventListener("hashchange", () => {
    const feature = featureFromHash();
    if (feature !== selectedFeature) select(feature);
  });
  select(featureFromHash());
}
