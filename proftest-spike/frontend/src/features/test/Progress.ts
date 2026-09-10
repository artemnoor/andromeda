export function renderProgress(current: number, total: number, label: string): HTMLElement {
  const wrapper = document.createElement("div");
  wrapper.className = "progress-wrap";
  const meta = document.createElement("div");
  meta.className = "progress-meta";
  const caption = document.createElement("span");
  caption.textContent = label;
  const count = document.createElement("span");
  count.textContent = `${current} / ${total}`;
  meta.append(caption, count);
  const progress = document.createElement("progress");
  progress.max = total;
  progress.value = current;
  progress.setAttribute("aria-label", `Прогресс: ${current} из ${total}`);
  wrapper.append(meta, progress);
  return wrapper;
}
