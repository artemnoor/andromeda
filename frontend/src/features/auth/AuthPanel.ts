import { ApiError } from "../../api/errors";
import { getAuthSession, loginAccount, logoutAccount, registerAccount, type AuthSessionResponse } from "../../api/client";

type AuthMode = "login" | "register";

export type AuthPanelCallbacks = Readonly<{
  onSessionChanged?: (session: AuthSessionResponse) => void;
  onNavigateToAccount?: () => void;
  onGuestContinue?: () => void;
}>;

const teardownByRoot = new WeakMap<HTMLElement, () => void>();

export function renderAuthPanel(root: HTMLElement, callbacks: AuthPanelCallbacks = {}): void {
  cleanupRoot(root);
  root.innerHTML = `<div class="profile-menu profile-menu-loading" data-testid="auth-panel"><button class="profile-trigger" data-testid="profile-menu-trigger" type="button" disabled aria-label="Проверяем статус профиля"><span class="profile-avatar" aria-hidden="true">${profileIconMarkup()}</span><span class="profile-trigger-copy"><strong>Профиль</strong><small>Проверяем…</small></span></button></div>`;
  void loadSession(root, callbacks);
}

async function loadSession(root: HTMLElement, callbacks: AuthPanelCallbacks): Promise<void> {
  try {
    renderState(root, await getAuthSession(), callbacks);
  } catch {
    renderState(root, { authenticated: false, account: null }, callbacks, "Не удалось проверить статус аккаунта. Можно продолжить как гость.");
  }
}

function renderState(root: HTMLElement, session: AuthSessionResponse, callbacks: AuthPanelCallbacks, statusMessage = ""): void {
  cleanupRoot(root);
  const account = session.authenticated && session.account ? session.account : null;
  const triggerLabel = account ? `Открыть меню профиля. ${account.email}` : "Открыть меню профиля. Вы вошли как гость";
  root.innerHTML = `<div class="profile-menu" data-testid="auth-panel"><button class="profile-trigger${account ? " profile-trigger-authenticated" : " profile-trigger-guest"}" data-testid="profile-menu-trigger" type="button" aria-haspopup="dialog" aria-expanded="false" aria-controls="profile-menu-panel" aria-label="${escapeAttribute(triggerLabel)}"><span class="profile-avatar" aria-hidden="true">${profileIconMarkup()}</span><span class="profile-trigger-copy"><strong>${account ? "Личный кабинет" : "Гость"}</strong><small>${account ? escapeHtml(account.email) : "Войти или создать аккаунт"}</small></span><span class="profile-trigger-chevron" aria-hidden="true">${chevronMarkup()}</span></button><div class="profile-menu-panel" data-testid="profile-menu-panel" id="profile-menu-panel" role="dialog" aria-label="Меню профиля" hidden></div></div>`;

  const menu = root.querySelector<HTMLElement>("[data-testid='profile-menu-panel']");
  const trigger = root.querySelector<HTMLButtonElement>("[data-testid='profile-menu-trigger']");
  if (!menu || !trigger) return;

  let isOpen = false;

  const focusPanel = (): void => {
    menu.querySelector<HTMLElement>("[data-profile-autofocus]")?.focus();
  };
  const setOpen = (open: boolean, restoreFocus = false): void => {
    isOpen = open;
    menu.hidden = !open;
    if (open) {
      menu.dataset.open = "true";
      trigger.setAttribute("aria-expanded", "true");
      focusPanel();
    } else {
      delete menu.dataset.open;
      trigger.setAttribute("aria-expanded", "false");
      if (restoreFocus) trigger.focus();
    }
  };
  const close = (): void => setOpen(false, true);

  const renderMenu = (): void => {
    menu.innerHTML = account ? renderAccountMenu(account) : renderGuestMenu(statusMessage);
    menu.querySelector<HTMLButtonElement>("[data-testid='auth-login-trigger']")?.addEventListener("click", () => {
      renderForm("login");
      setOpen(true);
    });
    menu.querySelector<HTMLButtonElement>("[data-testid='auth-register-trigger']")?.addEventListener("click", () => {
      renderForm("register");
      setOpen(true);
    });
    menu.querySelector<HTMLButtonElement>("[data-testid='auth-guest']")?.addEventListener("click", () => {
      close();
      callbacks.onGuestContinue?.();
    });
    menu.querySelector<HTMLButtonElement>("[data-testid='auth-account-link']")?.addEventListener("click", () => {
      close();
      callbacks.onNavigateToAccount?.();
    });
    menu.querySelector<HTMLButtonElement>("[data-testid='auth-logout']")?.addEventListener("click", async (event) => {
      const logoutButton = event.currentTarget as HTMLButtonElement;
      logoutButton.disabled = true;
      logoutButton.textContent = "Выходим…";
      try {
        const next = await logoutAccount();
        renderState(root, next, callbacks);
        callbacks.onSessionChanged?.(next);
      } catch {
        logoutButton.disabled = false;
        logoutButton.textContent = "Выйти";
        showPanelError(menu, "Не удалось завершить сессию. Попробуйте ещё раз.");
      }
    });
  };

  const renderForm = (mode: AuthMode): void => {
    const register = mode === "register";
    menu.innerHTML = `<div class="profile-menu-form"><div class="profile-menu-form-header"><button class="profile-menu-back" data-testid="auth-back" type="button" aria-label="Назад в меню профиля">${backMarkup()}</button><div><p class="eyebrow">${register ? "Новый аккаунт" : "Вход"}</p><strong>${register ? "Сохрани свой прогресс" : "С возвращением"}</strong></div></div><form data-testid="auth-form"><label for="auth-email"><span>Email</span><input id="auth-email" data-testid="auth-email" name="email" type="email" autocomplete="email" required data-profile-autofocus /></label><label for="auth-password"><span>Пароль</span><input id="auth-password" data-testid="auth-password" name="password" type="password" autocomplete="${register ? "new-password" : "current-password"}" required /></label><div class="auth-actions"><button class="primary-button" data-testid="auth-submit" type="submit">${register ? "Создать аккаунт" : "Войти"}</button><button class="secondary-button" data-testid="auth-mode-toggle" type="button">${register ? "Уже есть аккаунт" : "Создать аккаунт"}</button></div><p class="auth-error" data-testid="auth-error" role="alert" hidden></p><p class="auth-guest-note">Можно продолжить как гость — профиль сохранится в этой сессии.</p></form></div>`;
    menu.querySelector<HTMLButtonElement>("[data-testid='auth-back']")?.addEventListener("click", () => {
      renderMenu();
      setOpen(true);
    });
    menu.querySelector<HTMLButtonElement>("[data-testid='auth-mode-toggle']")?.addEventListener("click", () => {
      renderForm(register ? "login" : "register");
      setOpen(true);
    });
    menu.querySelector<HTMLFormElement>("[data-testid='auth-form']")?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget as HTMLFormElement;
      const values = new FormData(form);
      const email = values.get("email");
      const password = values.get("password");
      if (typeof email !== "string" || typeof password !== "string") return;
      const submit = menu.querySelector<HTMLButtonElement>("[data-testid='auth-submit']");
      if (submit) {
        submit.disabled = true;
        submit.textContent = register ? "Создаём…" : "Входим…";
      }
      try {
        const next = register ? await registerAccount({ email, password }) : await loginAccount({ email, password });
        renderState(root, next, callbacks);
        callbacks.onSessionChanged?.(next);
        callbacks.onNavigateToAccount?.();
      } catch (error: unknown) {
        renderForm(mode);
        showPanelError(menu, error instanceof ApiError ? error.payload.message : "Не удалось выполнить запрос.");
        setOpen(true);
      }
    });
  };

  const onTriggerClick = (): void => {
    if (isOpen) {
      close();
      return;
    }
    renderMenu();
    setOpen(true);
  };
  const onPointerDown = (event: PointerEvent): void => {
    if (isOpen && !root.contains(event.target as Node)) close();
  };
  const onKeyDown = (event: KeyboardEvent): void => {
    if (event.key === "Escape" && isOpen) {
      event.preventDefault();
      close();
    }
  };

  trigger.addEventListener("click", onTriggerClick);
  document.addEventListener("pointerdown", onPointerDown);
  document.addEventListener("keydown", onKeyDown);
  teardownByRoot.set(root, () => {
    trigger.removeEventListener("click", onTriggerClick);
    document.removeEventListener("pointerdown", onPointerDown);
    document.removeEventListener("keydown", onKeyDown);
  });
  renderMenu();
}

function renderGuestMenu(statusMessage: string): string {
  return `<div class="profile-menu-header"><p class="eyebrow">Личный кабинет</p><strong>Сохрани свой прогресс</strong><p>Войди или создай аккаунт, чтобы профиль, рекомендации и Personal Route возвращались вместе с тобой.</p></div><div class="profile-menu-actions"><button class="primary-button" data-testid="auth-login-trigger" data-profile-autofocus type="button">Войти</button><button class="secondary-button" data-testid="auth-register-trigger" type="button">Создать аккаунт</button></div><div class="profile-menu-divider"></div><button class="profile-menu-guest" data-testid="auth-guest" type="button"><span>Продолжить как гость</span><span aria-hidden="true">→</span></button>${statusMessage ? `<p class="profile-menu-status" role="status">${escapeHtml(statusMessage)}</p>` : ""}`;
}

function renderAccountMenu(account: NonNullable<AuthSessionResponse["account"]>): string {
  return `<div class="profile-menu-header"><p class="eyebrow">Твой аккаунт</p><strong data-testid="auth-account">${escapeHtml(account.email)}</strong><p>Профиль, рекомендации и личный маршрут сохраняются между сессиями.</p></div><div class="profile-menu-actions"><button class="primary-button" data-testid="auth-account-link" data-profile-autofocus type="button">Личный кабинет</button><button class="secondary-button" data-testid="auth-logout" type="button">Выйти</button></div>`;
}

function showPanelError(menu: HTMLElement, message: string): void {
  const error = menu.querySelector<HTMLElement>("[data-testid='auth-error']");
  if (error) {
    error.hidden = false;
    error.textContent = message;
    return;
  }
  const status = document.createElement("p");
  status.className = "profile-menu-status profile-menu-status-error";
  status.setAttribute("role", "alert");
  status.textContent = message;
  menu.append(status);
}

function cleanupRoot(root: HTMLElement): void {
  teardownByRoot.get(root)?.();
  teardownByRoot.delete(root);
}

function profileIconMarkup(): string {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="3.25"></circle><path d="M5.5 19.25c.85-3.1 3.1-4.65 6.5-4.65s5.65 1.55 6.5 4.65"></path></svg>`;
}

function chevronMarkup(): string {
  return `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m4 6 4 4 4-4"></path></svg>`;
}

function backMarkup(): string {
  return `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10.5 3.5 6 8l4.5 4.5"></path></svg>`;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}

function escapeAttribute(value: string): string {
  return escapeHtml(value);
}
