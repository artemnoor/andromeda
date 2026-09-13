import { expect, test, type Page } from "@playwright/test";

async function completeProfile(page: Page): Promise<void> {
  await page.getByTestId("personal-route-profile-link").click();
  await expect(page.getByTestId("proftest-start")).toBeVisible();
  await page.getByTestId("proftest-start").click();

  for (let index = 0; index < 6; index += 1) {
    await expect(page.getByTestId("proftest-progress")).toContainText(`${index + 1} / 6`);
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

test.describe("personal route vertical slice", () => {
  test("requires a profile and renders logical program/event steps", async ({ page }) => {
    await page.goto("/#personal-route");
    await expect(page.getByTestId("nav-personal-route")).toHaveClass(/active/);
    await expect(page.getByTestId("personal-route-profile-required")).toBeVisible();

    await completeProfile(page);
    await page.goto("/#personal-route");
    await expect(page.getByTestId("personal-route-results")).toBeVisible();
    await expect(page.getByTestId("personal-route-step").first()).toBeVisible();
    await expect(page.locator("[data-step-kind='explore_program']")).toBeVisible();

    const eventSteps = page.locator("[data-step-kind='attend_event']");
    if (await eventSteps.count() > 0) {
      await expect(eventSteps.first()).toContainText("Посетить событие");
      if (await page.getByTestId("personal-route-point").count() > 0) await expect(page.getByTestId("personal-route-point").first()).toBeVisible();
      if (await page.getByTestId("personal-route-registration").count() > 0) await expect(page.getByTestId("personal-route-registration").first()).toHaveAttribute("href", /^https:\/\//);
    } else {
      await expect(page.getByTestId("personal-route-no-events")).toBeVisible();
    }
  });

  test.describe("mobile viewport", () => {
    test.use({ viewport: { width: 390, height: 844 } });

    test("keeps the logical plan readable without horizontal overflow", async ({ page }) => {
      await page.goto("/#personal-route");
      await page.waitForSelector("[data-testid='personal-route-profile-required'], [data-testid='personal-route-results'], [data-testid='personal-route-error']", { state: "visible" });
      if (await page.getByTestId("personal-route-profile-required").isVisible().catch(() => false)) await completeProfile(page);
      await page.goto("/#personal-route");
      await expect(page.getByTestId("personal-route-results")).toBeVisible();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      expect(overflow).toBe(false);
      await expect(page.getByTestId("nav-personal-route")).toBeVisible();
    });
  });
});
