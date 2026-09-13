import type { AnswerPayload, QuestionResponse } from "../../api/generated";
import { renderProgress } from "./Progress";

interface QuestionProps {
  question: QuestionResponse;
  index: number;
  total: number;
  selected: AnswerPayload[];
  onSelect: (optionId: string) => void;
  onIntensity: (optionId: string, intensity: number) => void;
  onBack: () => void;
  onNext: () => void;
}

export function renderQuestionScreen(props: QuestionProps): HTMLElement {
  const section = document.createElement("section");
  section.className = "question-shell";
  section.dataset.testid = "question-screen";
  const header = document.createElement("div");
  header.className = "screen-header";
  const eyebrow = document.createElement("span");
  eyebrow.className = "eyebrow";
  eyebrow.textContent = props.question.block === "anti_interests" ? "Шаг 5 · честное ограничение" : props.question.block === "tradeoff" ? "Шаг 4 · способ думать" : props.question.block === "activity" ? "Шаг 3 · способ работать" : "Шаг 1–2 · интересы";
  const title = document.createElement("h1");
  title.textContent = props.question.title;
  header.append(eyebrow, title);
  section.append(header, renderProgress(props.index + 1, props.total, "Профиль программы"));
  const prompt = document.createElement("div");
  prompt.className = "question-prompt";
  const heading = document.createElement("h2");
  heading.textContent = props.question.prompt;
  const helper = document.createElement("p");
  helper.textContent = props.question.helperText;
  prompt.append(heading, helper);
  section.append(prompt);

  const options = document.createElement("div");
  options.className = props.question.kind === "multi_intensity" ? "option-grid option-grid--dense" : "option-grid";
  for (const option of props.question.options) {
    const selected = props.selected.some((answer) => answer.optionId === option.id);
    const card = document.createElement("div");
    card.className = `option-card${selected ? " option-card--selected" : ""}`;
    const button = document.createElement("button");
    button.className = "option-button";
    button.type = "button";
    button.dataset.testid = `question-option-${option.id}`;
    button.setAttribute("aria-pressed", String(selected));
    const label = document.createElement("strong");
    label.textContent = option.label;
    const description = document.createElement("span");
    description.textContent = option.description;
    const indicator = document.createElement("span");
    indicator.className = "option-indicator";
    indicator.setAttribute("aria-hidden", "true");
    button.append(label, description, indicator);
    button.addEventListener("click", () => props.onSelect(option.id));
    card.append(button);
    if (option.requiresIntensity && selected) {
      const answer = props.selected.find((item) => item.optionId === option.id);
      const rangeLabel = document.createElement("label");
      rangeLabel.className = "intensity-control";
      rangeLabel.textContent = "Насколько сильно?";
      const range = document.createElement("input");
      range.type = "range";
      range.min = "0.2";
      range.max = "1";
      range.step = "0.05";
      range.value = String(answer?.intensity ?? 0.5);
      range.dataset.testid = `intensity-${option.id}`;
      range.setAttribute("aria-label", `Сила антиинтереса: ${option.label}`);
      range.addEventListener("input", () => props.onIntensity(option.id, Number(range.value)));
      rangeLabel.append(range);
      card.append(rangeLabel);
    }
    options.append(card);
  }
  section.append(options);

  const footer = document.createElement("div");
  footer.className = "screen-footer";
  const back = document.createElement("button");
  back.className = "button button--ghost";
  back.type = "button";
  back.dataset.testid = "back-button";
  back.textContent = "Назад";
  back.addEventListener("click", props.onBack);
  const next = document.createElement("button");
  next.className = "button button--primary";
  next.type = "button";
  next.dataset.testid = "next-button";
  next.textContent = props.index === props.total - 1 ? "Сравнить программы" : "Дальше";
  next.disabled = props.question.kind !== "multi_intensity" && props.selected.length === 0;
  next.addEventListener("click", props.onNext);
  footer.append(back, next);
  section.append(footer);
  return section;
}
