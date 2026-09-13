import type { AreaCode, Recommendation } from "../../api/generated";
import { asNumber, type ApiNumber } from "../../api/numeric";

const AREA_LABELS: Partial<Record<AreaCode, string>> = {
  mathematics_statistics: "Математика и статистика",
  computer_science_data: "Компьютерные науки и данные",
  physics_astronomy: "Физика и астрономия",
  chemistry_materials: "Химия и материалы",
  biology_biotechnology: "Биология и биотехнологии",
  earth_environment: "Земля, экология и окружающая среда",
  engineering_technology: "Инженерия и технологии",
  architecture_construction: "Архитектура, строительство и урбанистика",
  agriculture_veterinary: "Сельское хозяйство и ветеринария",
  medicine_health: "Медицина и здоровье",
  psychology_cognitive: "Психология и когнитивные науки",
  society_social_sciences: "Общество и социальные науки",
  economics_finance: "Экономика и финансы",
  business_management: "Бизнес и управление",
  law_policy_public_administration: "Право, политика и госуправление",
  languages_linguistics_literature: "Языки, лингвистика и литература",
  history_philosophy_humanities: "История, философия и гуманитарные науки",
  art_design_media: "Искусство, дизайн и медиа",
  education_pedagogy: "Образование и педагогика",
  sport_tourism_hospitality: "Спорт, туризм и гостеприимство",
  safety_defense_transport: "Безопасность, оборона и транспорт",
  universal_interdisciplinary: "Универсальные дисциплины"
};

export function renderResultDetail(recommendation: Recommendation, onBack: () => void): HTMLElement {
  const section = document.createElement("section");
  section.className = "detail-shell";
  section.dataset.testid = "result-detail";
  const back = document.createElement("button");
  back.className = "button button--ghost";
  back.type = "button";
  back.dataset.testid = "detail-back";
  back.textContent = "← Все рекомендации";
  back.addEventListener("click", onBack);
  const eyebrow = document.createElement("span");
  eyebrow.className = "eyebrow eyebrow--accent";
  eyebrow.textContent = "Подробное объяснение";
  const title = document.createElement("h1");
  title.textContent = recommendation.program.programCode;
  const name = document.createElement("p");
  name.className = "lead-copy";
  name.textContent = recommendation.program.programName;
  const score = document.createElement("div");
  score.className = "detail-score";
  score.textContent = `${recommendation.contentFit} / 100 Content Fit`;
  section.append(back, eyebrow, title, name, score);

  const breakdown = document.createElement("div");
  breakdown.className = "breakdown-grid";
  for (const [label, value] of [
    ["Предметный fit", recommendation.breakdown.subjectFit],
    ["Способ работы", recommendation.breakdown.activityFit],
    ["Отличительные дисциплины", recommendation.breakdown.distinctiveFit],
    ["Anti-interest penalty", recommendation.breakdown.antiPenalty]
  ] as const) {
    const item = document.createElement("div");
    item.className = "breakdown-item";
    const itemLabel = document.createElement("span");
    itemLabel.textContent = label;
    const itemValue = document.createElement("strong");
    itemValue.textContent = `${Math.round(asNumber(value))}`;
    item.append(itemLabel, itemValue);
    breakdown.append(item);
  }
  section.append(breakdown);
  section.append(renderOptionalMetrics(recommendation));

  const reasonsTitle = document.createElement("h2");
  reasonsTitle.textContent = "Почему так";
  section.append(reasonsTitle);
  const reasons = document.createElement("div");
  reasons.className = "detail-reasons";
  for (const reason of recommendation.reasons) {
    const item = document.createElement("article");
    item.className = `detail-reason${reason.kind === "negative" ? " detail-reason--negative" : ""}`;
    const heading = document.createElement("h3");
    heading.textContent = reason.title;
    const detail = document.createElement("p");
    detail.textContent = reason.detail;
    item.append(heading, detail);
    if (reason.sourceNames.length) {
      const evidence = document.createElement("small");
      evidence.textContent = `Источник в плане: ${reason.sourceNames.join(", ")}`;
      item.append(evidence);
    }
    reasons.append(item);
  }
  section.append(reasons);

  const plan = document.createElement("div");
  plan.className = "plan-summary";
  const planTitle = document.createElement("h2");
  planTitle.textContent = "Состав учебного плана";
  plan.append(planTitle, renderDistribution("Основные блоки", recommendation.program.areaShare, AREA_LABELS), renderDistribution("По семестрам", recommendation.program.semesterDistribution));
  const distinctiveTitle = document.createElement("h2");
  distinctiveTitle.textContent = "Отличительные дисциплины";
  plan.append(distinctiveTitle);
  const disciplines = document.createElement("ul");
  disciplines.className = "discipline-list";
  for (const subject of recommendation.program.distinctiveSubjects) {
    const item = document.createElement("li");
    const subjectName = document.createElement("strong");
    subjectName.textContent = subject.sourceName;
    const subjectShare = document.createElement("span");
    subjectShare.textContent = `${Math.round(asNumber(subject.share) * 100)}% нагрузки`;
    item.append(subjectName, subjectShare);
    disciplines.append(item);
  }
  if (!recommendation.program.distinctiveSubjects.length) {
    const empty = document.createElement("p");
    empty.textContent = "Для этого каталога отличительные дисциплины пока не выделены.";
    disciplines.append(empty);
  }
  plan.append(disciplines);
  section.append(plan);
  return section;
}

function renderOptionalMetrics(recommendation: Recommendation): HTMLElement {
  const panel = document.createElement("section");
  panel.className = "optional-metrics";
  panel.dataset.testid = "optional-metrics";
  const title = document.createElement("h2");
  title.textContent = "Дополнительные показатели";
  const note = document.createElement("p");
  note.textContent = "Они не влияют на Content Fit и пока не рассчитываются в Spike.";
  const list = document.createElement("div");
  list.className = "optional-metrics-list";
  for (const metric of recommendation.metrics) {
    const row = document.createElement("div");
    row.className = "optional-metric";
    const label = document.createElement("span");
    label.textContent = metric.label;
    const value = document.createElement("strong");
    value.textContent = metric.status === "not_available" ? "Пока недоступно" : `${metric.value ?? 0} / 100`;
    row.append(label, value);
    list.append(row);
  }
  panel.append(title, note, list);
  return panel;
}

function renderDistribution(label: string, values: Partial<Record<string, ApiNumber>>, labels: Partial<Record<string, string>> = {}): HTMLElement {
  const wrapper = document.createElement("div");
  wrapper.className = "distribution-block";
  const title = document.createElement("h3");
  title.textContent = label;
  wrapper.append(title);
  for (const [code, value] of Object.entries(values).sort(([, left], [, right]) => asNumber(right) - asNumber(left)).slice(0, 8)) {
    const row = document.createElement("div");
    row.className = "distribution-row";
    const name = document.createElement("span");
    name.textContent = labels[code] ?? (code === "unassigned" ? "Без семестра" : `Семестр ${code}`);
    const percent = document.createElement("strong");
    percent.textContent = `${Math.round(asNumber(value) * 100)}%`;
    row.append(name, percent);
    wrapper.append(row);
  }
  return wrapper;
}
