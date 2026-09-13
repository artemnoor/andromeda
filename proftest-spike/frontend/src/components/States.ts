export function renderLoading(label = "Загружаем учебные планы"): HTMLElement {
  const section = document.createElement("section");
  section.className = "state-card state-card--loading";
  section.dataset.testid = "loading-state";
  section.setAttribute("aria-live", "polite");
  const spinner = document.createElement("span");
  spinner.className = "spinner";
  spinner.setAttribute("aria-hidden", "true");
  const title = document.createElement("h2");
  title.textContent = label;
  section.append(spinner, title);
  return section;
}

export function renderError(message: string, onRetry: () => void): HTMLElement {
  const section = document.createElement("section");
  section.className = "state-card state-card--error";
  section.dataset.testid = "error-state";
  const eyebrow = document.createElement("span");
  eyebrow.className = "eyebrow eyebrow--danger";
  eyebrow.textContent = "Связь с API";
  const title = document.createElement("h2");
  title.textContent = "Не получилось загрузить данные";
  const body = document.createElement("p");
  body.textContent = message;
  const button = document.createElement("button");
  button.className = "button button--secondary";
  button.type = "button";
  button.textContent = "Повторить";
  button.addEventListener("click", onRetry);
  section.append(eyebrow, title, body, button);
  return section;
}

export function renderEmpty(message: string, onRestart: () => void): HTMLElement {
  const section = document.createElement("section");
  section.className = "state-card state-card--empty";
  section.dataset.testid = "empty-state";
  const eyebrow = document.createElement("span");
  eyebrow.className = "eyebrow";
  eyebrow.textContent = "Каталог пока мал";
  const title = document.createElement("h2");
  title.textContent = "Нет программ для сравнения";
  const body = document.createElement("p");
  body.textContent = message;
  const button = document.createElement("button");
  button.className = "button button--secondary";
  button.type = "button";
  button.textContent = "Начать заново";
  button.addEventListener("click", onRestart);
  section.append(eyebrow, title, body, button);
  return section;
}
