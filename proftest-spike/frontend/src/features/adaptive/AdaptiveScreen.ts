import type { AdaptiveQuestion } from "../../api/generated";
import { renderProgress } from "../test/Progress";

interface AdaptiveProps {
  question: AdaptiveQuestion | null;
  skippedReason: string | null;
  selectedId: string | null;
  onSelect: (optionId: "more_first" | "balanced" | "more_second") => void;
  onBack: () => void;
  onNext: () => void;
}

export function renderAdaptiveScreen(props: AdaptiveProps): HTMLElement {
  const section = document.createElement("section");
  section.className = "question-shell adaptive-shell";
  section.dataset.testid = "adaptive-screen";
  const eyebrow = document.createElement("span");
  eyebrow.className = "eyebrow eyebrow--accent";
  eyebrow.textContent = "Адаптивное уточнение";
  const title = document.createElement("h1");
  title.textContent = props.question ? "Один вопрос, который различает программы" : "Уточнение не требуется";
  section.append(eyebrow, title, renderProgress(7, 7, "Финальный штрих"));
  if (!props.question) {
    const reason = document.createElement("p");
    reason.className = "lead-copy";
    reason.textContent = props.skippedReason ?? "В текущем каталоге недостаточно различий для честного вопроса.";
    section.append(reason);
  } else {
    const prompt = document.createElement("div");
    prompt.className = "question-prompt";
    const heading = document.createElement("h2");
    heading.textContent = props.question.prompt;
    const helper = document.createElement("p");
    helper.textContent = props.question.helperText;
    prompt.append(heading, helper);
    section.append(prompt);
    const options = document.createElement("div");
    options.className = "option-grid option-grid--adaptive";
    for (const option of props.question.options) {
      const button = document.createElement("button");
      button.className = `option-card option-button${props.selectedId === option.id ? " option-card--selected" : ""}`;
      button.type = "button";
      button.dataset.testid = `adaptive-option-${option.id}`;
      button.setAttribute("aria-pressed", String(props.selectedId === option.id));
      const label = document.createElement("strong");
      label.textContent = option.label;
      const detail = document.createElement("span");
      detail.textContent = option.description;
      button.append(label, detail);
      button.addEventListener("click", () => props.onSelect(option.id));
      options.append(button);
    }
    section.append(options);
  }
  const footer = document.createElement("div");
  footer.className = "screen-footer";
  const back = document.createElement("button");
  back.className = "button button--ghost";
  back.type = "button";
  back.dataset.testid = "adaptive-back";
  back.textContent = "Назад";
  back.addEventListener("click", props.onBack);
  const next = document.createElement("button");
  next.className = "button button--primary";
  next.type = "button";
  next.dataset.testid = "adaptive-next";
  next.textContent = "Показать результат";
  next.disabled = Boolean(props.question && !props.selectedId);
  next.addEventListener("click", props.onNext);
  footer.append(back, next);
  section.append(footer);
  return section;
}
