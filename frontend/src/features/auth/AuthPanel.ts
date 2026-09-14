import { ApiError } from "../../api/errors";
import { getAuthSession, loginAccount, logoutAccount, registerAccount, type AuthSessionResponse } from "../../api/client";

type AuthMode = "login" | "register";

export function renderAuthPanel(root: HTMLElement, onSessionChanged: (session: AuthSessionResponse) => void = () => undefined): void {
  root.innerHTML = `<section class="auth-panel" data-testid="auth-panel" aria-live="polite"><p class="auth-status" data-testid="auth-loading">Проверяем аккаунт…</p></section>`;
  void loadSession(root, onSessionChanged);
}

async function loadSession(root: HTMLElement, onSessionChanged: (session: AuthSessionResponse) => void): Promise<void> {
  try {
    renderState(root, await getAuthSession(), onSessionChanged);
  } catch {
    renderError(root, "Не удалось проверить аккаунт. Попробуйте ещё раз.", onSessionChanged);
  }
}

function renderState(root: HTMLElement, session: AuthSessionResponse, onSessionChanged: (session: AuthSessionResponse) => void): void {
  if (session.authenticated && session.account) {
    root.innerHTML = `<section class="auth-panel auth-panel-account" data-testid="auth-panel"><div><p class="eyebrow">Аккаунт</p><strong data-testid="auth-account">${escapeHtml(session.account.email)}</strong><small>${escapeHtml(session.account.accountId)}</small></div><button class="secondary-button" data-testid="auth-logout" type="button">Выйти</button></section>`;
    root.querySelector<HTMLButtonElement>("[data-testid='auth-logout']")?.addEventListener("click", async () => {
      setLoading(root);
      try {
        const next = await logoutAccount();
        renderState(root, next, onSessionChanged);
        onSessionChanged(next);
      } catch {
        renderError(root, "Не удалось завершить сессию.", onSessionChanged);
      }
    });
    return;
  }
  renderForm(root, "login", onSessionChanged);
}

function renderForm(root: HTMLElement, mode: AuthMode, onSessionChanged: (session: AuthSessionResponse) => void): void {
  const register = mode === "register";
  root.innerHTML = `<section class="auth-panel" data-testid="auth-panel"><div class="auth-copy"><p class="eyebrow">${register ? "Новый аккаунт" : "Аккаунт"}</p><strong>${register ? "Сохраните профиль между сессиями" : "Войдите, чтобы восстановить профиль"}</strong></div><form data-testid="auth-form"><label>Email<input data-testid="auth-email" name="email" type="email" autocomplete="email" required /></label><label>Пароль<input data-testid="auth-password" name="password" type="password" autocomplete="${register ? "new-password" : "current-password"}" required /></label><div class="auth-actions"><button class="primary-button" data-testid="auth-submit" type="submit">${register ? "Зарегистрироваться" : "Войти"}</button><button class="secondary-button" data-testid="auth-mode-toggle" type="button">${register ? "Уже есть аккаунт" : "Создать аккаунт"}</button></div><p class="auth-error" data-testid="auth-error" hidden></p></form></section>`;
  root.querySelector<HTMLButtonElement>("[data-testid='auth-mode-toggle']")?.addEventListener("click", () => renderForm(root, register ? "login" : "register", onSessionChanged));
  root.querySelector<HTMLFormElement>("[data-testid='auth-form']")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget as HTMLFormElement;
    const values = new FormData(form);
    const email = values.get("email");
    const password = values.get("password");
    if (typeof email !== "string" || typeof password !== "string") return;
    setLoading(root);
    try {
      const session = register ? await registerAccount({ email, password }) : await loginAccount({ email, password });
      form.reset();
      renderState(root, session, onSessionChanged);
      onSessionChanged(session);
    } catch (error: unknown) {
      renderError(root, error instanceof ApiError ? error.payload.message : "Не удалось выполнить запрос.", onSessionChanged, mode);
    }
  });
}

function setLoading(root: HTMLElement): void {
  root.innerHTML = `<section class="auth-panel" data-testid="auth-panel"><p class="auth-status" data-testid="auth-loading">Обновляем сессию…</p></section>`;
}

function renderError(root: HTMLElement, message: string, onSessionChanged: (session: AuthSessionResponse) => void, mode: AuthMode = "login"): void {
  renderForm(root, mode, onSessionChanged);
  const error = root.querySelector<HTMLElement>("[data-testid='auth-error']");
  if (error) {
    error.hidden = false;
    error.textContent = message;
  }
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}
