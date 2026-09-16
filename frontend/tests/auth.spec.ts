import { expect, test, type Page } from "@playwright/test";

async function openProfileMenu(page: Page): Promise<void> {
  const panel = page.getByTestId("profile-menu-panel");
  const trigger = page.getByTestId("profile-menu-trigger");
  await expect(trigger).toHaveAttribute("aria-expanded", "false");
  await trigger.click();
  await expect(panel).toBeVisible();
}

test("registers, logs in again, and logs out from the profile menu", async ({ page }, testInfo) => {
  const email = `browser-${testInfo.project.name}-${Date.now()}@example.com`;
  const password = "a-secure-browser-password";
  await page.goto("/#catalog");
  await expect(page.getByTestId("auth-panel")).toBeVisible();
  await openProfileMenu(page);
  await page.getByTestId("auth-register-trigger").click();
  await page.getByTestId("auth-email").fill(email);
  await page.getByTestId("auth-password").fill(password);
  await page.getByTestId("auth-submit").click();
  await expect(page).toHaveURL(/#account/);
  await expect(page.getByTestId("account-page")).toBeVisible();
  await openProfileMenu(page);
  await expect(page.getByTestId("auth-account")).toHaveText(email);

  await page.getByTestId("auth-logout").click();
  await expect(page.getByTestId("profile-menu-panel")).toBeHidden();
  await openProfileMenu(page);
  await expect(page.getByTestId("auth-login-trigger")).toBeVisible();
  await page.getByTestId("auth-login-trigger").click();
  await page.getByTestId("auth-email").fill(email);
  await page.getByTestId("auth-password").fill(password);
  await page.getByTestId("auth-submit").click();
  await expect(page).toHaveURL(/#account/);
  await expect(page.getByTestId("account-page")).toBeVisible();
  await openProfileMenu(page);
  await expect(page.getByTestId("auth-account")).toHaveText(email);

  await page.getByTestId("auth-logout").click();
  await expect(page.getByTestId("profile-menu-panel")).toBeHidden();
});

test("keeps the guest path available from the profile menu", async ({ page }) => {
  await page.goto("/#catalog");
  await openProfileMenu(page);
  await expect(page.getByTestId("auth-guest")).toBeVisible();
  await page.getByTestId("auth-guest").click();
  await expect(page.getByTestId("profile-menu-panel")).toBeHidden();
  await expect(page.getByTestId("catalog-page")).toBeVisible();
});

test.describe("mobile profile menu", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("does not overflow horizontally", async ({ page }) => {
    await page.goto("/#catalog");
    await expect(page.getByTestId("profile-menu-trigger")).toBeVisible();
    await openProfileMenu(page);
    await expect(page.getByTestId("auth-guest")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
  });
});
