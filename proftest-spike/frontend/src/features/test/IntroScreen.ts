import type { BootstrapResponse } from "../../api/generated";

interface IntroProps {
  bootstrap: BootstrapResponse;
  hasDraft: boolean;
  onStart: () => void;
  onResume: () => void;
}

export function renderIntroScreen(props: IntroProps): HTMLElement {
  const section = document.createElement("section");
  section.className = "hero-card";
  section.dataset.testid = "intro-screen";
  const copy = document.createElement("div");
  copy.className = "hero-copy";
  const eyebrow = document.createElement("span");
  eyebrow.className = "eyebrow";
  eyebrow.textContent = "Andromeda · рабочий Spike";
  const title = document.createElement("h1");
  title.textContent = "Найди программу, содержание которой тебе подходит";
  const body = document.createElement("p");
  body.textContent = "Короткий сценарный тест сопоставит твои интересы и способ работы с реальными учебными планами. Это не диагноз и не название профессии — только честное сравнение содержания обучения.";
  const actions = document.createElement("div");
  actions.className = "button-row";
  const start = document.createElement("button");
  start.className = "button button--primary";
  start.type = "button";
  start.dataset.testid = "start-test";
  start.textContent = props.hasDraft ? "Начать новый тест" : "Начать тест";
  start.addEventListener("click", props.onStart);
  actions.append(start);
  if (props.hasDraft) {
    const resume = document.createElement("button");
    resume.className = "button button--secondary";
    resume.type = "button";
    resume.dataset.testid = "resume-test";
    resume.textContent = "Продолжить";
    resume.addEventListener("click", props.onResume);
    actions.append(resume);
  }
  copy.append(eyebrow, title, body, actions);

  const aside = document.createElement("aside");
  aside.className = "hero-aside";
  const marker = document.createElement("div");
  marker.className = "hero-marker";
  marker.textContent = "01";
  const asideTitle = document.createElement("h2");
  asideTitle.textContent = "Содержание, а не ярлык";
  const asideText = document.createElement("p");
  asideText.textContent = `${props.bootstrap.totalBase} базовых шагов · примерно 8–12 минут`;
  const tags = document.createElement("div");
  tags.className = "tag-list";
  for (const tagText of ["интересы", "способ работы", "антиинтересы", "уточнение"]) {
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.textContent = tagText;
    tags.append(tag);
  }
  aside.append(marker, asideTitle, asideText, tags);
  section.append(copy, aside);
  return section;
}
