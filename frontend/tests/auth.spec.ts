import { expect, test, type Page } from "@playwright/test";

async function completeProftest(page: Page): Promise<void> {
  await page.getByTestId("nav-proftest").click();
  await expect(page.getByTestId("proftest-start")).toBeVisible();
  await page.getByTestId("proftest-start").click();
  for (let index = 0; index < 6; index += 1) {
    await page.locator(".choice-card").first().click();
    await page.getByTestId("proftest-next").click();
  }
  await page.waitForSelector("[data-testid='adaptive-submit'], [data-testid='adaptive-skipped-continue'], [data-testid='proftest-results']", { state: "visible" });
  const adaptive = page.locator("[data-testid='adaptive-submit']");
  if (await adaptive.isVisible().catch(() => false)) {
    await page.locator("[data-adaptive-option]").first().click();
    await adaptive.click();
  } else {
    const skipped = page.getByTestId("adaptive-skipped-continue");
    if (await skipped.isVisible().catch(() => false)) await skipped.click();
  }
  await expect(page.getByTestId("proftest-results")).toBeVisible();
}

test("registers, restores account-backed profile, and logs out", async ({ page }, testInfo) => {
  const email = `browser-${testInfo.project.name}-${Date.now()}@example.com`;
  const password = "a-secure-browser-password";
  await page.goto("/");
  await expect(page.getByTestId("auth-panel")).toBeVisible();
  await page.getByTestId("auth-mode-toggle").click();
  await page.getByTestId("auth-email").fill(email);
  await page.getByTestId("auth-password").fill(password);
  await page.getByTestId("auth-submit").click();
  await expect(page.getByTestId("auth-account")).toHaveText(email);

  await completeProftest(page);
  await page.getByTestId("auth-logout").click();
  await expect(page.getByTestId("auth-submit")).toBeVisible();
  await page.getByTestId("auth-email").fill(email);
  await page.getByTestId("auth-password").fill(password);
  await page.getByTestId("auth-submit").click();
  await expect(page.getByTestId("auth-account")).toHaveText(email);

  await page.reload();
  await page.getByTestId("nav-proftest").click();
  await expect(page.getByTestId("profile-restored")).toBeVisible();
  await page.getByTestId("auth-logout").click();
  await expect(page.getByTestId("auth-submit")).toBeVisible();
});

test.describe("mobile auth panel", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("does not overflow horizontally", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("auth-panel")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
  });
});
