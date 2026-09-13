import type { AreaCode, Recommendation, ResultsResponse } from "../../api/generated";
import { asNumber } from "../../api/numeric";

interface ResultsProps {
  results: ResultsResponse;
  onDetail: (recommendation: Recommendation) => void;
  onRestart: () => void;
}

const AREA_LABELS: Partial<Record<AreaCode, string>> = {
  mathematics_statistics: "Математика",
  computer_science_data: "Компьютерные науки и данные",
  physics_astronomy: "Физика",
  chemistry_materials: "Химия и материалы",
  biology_biotechnology: "Биология",
  earth_environment: "Земля и окружающая среда",
  engineering_technology: "Инженерия и технологии",
  architecture_construction: "Архитектура и строительство",
  agriculture_veterinary: "Сельское хозяйство",
  medicine_health: "Медицина и здоровье",
  psychology_cognitive: "Психология",
  society_social_sciences: "Общество и социальные науки",
  economics_finance: "Экономика и финансы",
  business_management: "Бизнес и управление",
  law_policy_public_administration: "Право и госуправление",
  languages_linguistics_literature: "Языки",
  history_philosophy_humanities: "Гуманитарные науки",
  art_design_media: "Искусство и дизайн",
  education_pedagogy: "Образование и педагогика",
  sport_tourism_hospitality: "Спорт и туризм",
  safety_defense_transport: "Безопасность и транспорт",
  universal_interdisciplinary: "Междисциплинарные"
};

export function renderResultsScreen(props: ResultsProps): HTMLElement {
  const section = document.createElement("section");
  section.className = "results-shell";
  section.dataset.testid = "results-screen";
  const header = document.createElement("div");
  header.className = "results-heading";
  const eyebrow = document.createElement("span");
  eyebrow.className = "eyebrow eyebrow--accent";
  eyebrow.textContent = "Твой shortlist";
  const title = document.createElement("h1");
  title.textContent = "Программы, совпадающие с содержанием профиля";
  const note = document.createElement("p");
  note.textContent = `${props.results.note} Доступно программ в каталоге: ${props.results.catalogProgramCount}.`;
  header.append(eyebrow, title, note);
  const actions = document.createElement("div");
  actions.className = "button-row button-row--compact";
  const restart = document.createElement("button");
  restart.className = "button button--secondary";
  restart.type = "button";
  restart.dataset.testid = "restart-test";
  restart.textContent = "Пройти снова";
  restart.addEventListener("click", props.onRestart);
  actions.append(restart);
  header.append(actions);
  section.append(header);
  const list = document.createElement("div");
  list.className = "results-list";
  for (const recommendation of props.results.recommendations) list.append(renderRecommendation(recommendation, props.onDetail));
  section.append(list);
  return section;
}

function renderRecommendation(recommendation: Recommendation, onDetail: (recommendation: Recommendation) => void): HTMLElement {
  const article = document.createElement("article");
  article.className = "recommendation-card";
  article.dataset.testid = "recommendation-card";
  const rank = document.createElement("span");
  rank.className = "rank-number";
  rank.textContent = String(recommendation.rank).padStart(2, "0");
  const content = document.createElement("div");
  content.className = "recommendation-content";
  const titleRow = document.createElement("div");
  titleRow.className = "recommendation-title-row";
  const title = document.createElement("h2");
  title.textContent = recommendation.program.programCode;
  const score = document.createElement("div");
  score.className = "score-badge";
  score.textContent = `${recommendation.contentFit} / 100`;
  titleRow.append(title, score);
  const name = document.createElement("p");
  name.className = "program-name";
  name.textContent = recommendation.program.programName;
  const fit = document.createElement("div");
  fit.className = "fit-bar";
  const fitFill = document.createElement("span");
  fitFill.style.width = `${recommendation.contentFit}%`;
  fit.append(fitFill);
  const reasons = document.createElement("ul");
  reasons.className = "reason-list";
  reasons.dataset.testid = "reason-list";
  for (const reason of recommendation.reasons.slice(0, 3)) {
    const item = document.createElement("li");
    item.className = reason.kind === "negative" ? "reason reason--negative" : "reason";
    const mark = document.createElement("span");
    mark.className = "reason-mark";
    mark.textContent = reason.kind === "negative" ? "−" : "+";
    const text = document.createElement("span");
    text.textContent = reason.title;
    item.append(mark, text);
    reasons.append(item);
  }
  const summary = document.createElement("div");
  summary.className = "summary-row";
  summary.append(renderAreaTags(recommendation), renderMetricTags(recommendation));
  const detail = document.createElement("button");
  detail.className = "button button--ghost button--small";
  detail.type = "button";
  detail.dataset.testid = "open-detail";
  detail.textContent = "Открыть объяснение →";
  detail.addEventListener("click", () => onDetail(recommendation));
  content.append(titleRow, name, fit, reasons, summary, detail);
  article.append(rank, content);
  return article;
}

function renderAreaTags(recommendation: Recommendation): HTMLElement {
  const wrapper = document.createElement("div");
  wrapper.className = "tag-list tag-list--summary";
  const entries = Object.entries(recommendation.program.areaShare).sort(([, left], [, right]) => asNumber(right) - asNumber(left)).slice(0, 3);
  for (const [code, share] of entries) {
    const tag = document.createElement("span");
    tag.className = "tag tag--muted";
    tag.textContent = `${AREA_LABELS[code as AreaCode] ?? code} ${Math.round(asNumber(share) * 100)}%`;
    wrapper.append(tag);
  }
  return wrapper;
}

function renderMetricTags(recommendation: Recommendation): HTMLElement {
  const wrapper = document.createElement("div");
  wrapper.className = "metric-list";
  const workload = document.createElement("span");
  workload.className = "metric-pill";
  workload.textContent = recommendation.program.basis === "hours" ? `${recommendation.program.totalHours} ч` : `${recommendation.program.totalCredits} ЗЕТ`;
  wrapper.append(workload);
  return wrapper;
}
