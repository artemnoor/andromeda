import { expect, test, type Page } from "@playwright/test";

async function completeTest(page: Page): Promise<void> {
  await page.goto("/#proftest");
  await expect(page.getByTestId("proftest-start")).toBeVisible();
  await page.getByTestId("proftest-start").click();
  for (let index = 0; index < 38; index += 1) {
    const questionOrResults = page.getByTestId("session-question").or(page.getByTestId("proftest-results"));
    await expect(questionOrResults).toBeVisible();
    if (await page.getByTestId("proftest-results").isVisible()) break;
    await page.locator(".choice-card").first().click();
    await page.getByTestId("session-next").click();
  }
  await expect(page.getByTestId("proftest-results")).toBeVisible();
}

test.describe("recommendation vertical slice", () => {
  test("shows Content Fit, real plan details and explainable reasons", async ({ page }) => {
    await completeTest(page);
    await expect(page.getByText("Content Fit").first()).toBeVisible();
    await expect(page.locator("[data-testid='result-card']").first()).toBeVisible();
    await page.locator("[data-result-detail='0']").click();
    await expect(page.getByTestId("proftest-detail-card")).toBeVisible();
    await expect(page.getByText("Почему подходит")).toBeVisible();
    await expect(page.getByText("Семестры")).toBeVisible();
    await expect(page.getByText(/Workload readiness/)).toBeVisible();
  });

  test("restores current recommendations after a page reload", async ({ page }) => {
    await completeTest(page);
    await page.evaluate(() => window.localStorage.removeItem("andromeda:proftest:v1"));
    await page.reload();
    await expect(page.getByTestId("profile-restored")).toBeVisible();
    await expect(page.getByTestId("proftest-results")).toBeVisible();
  });

  test("keeps recommendation detail readable without horizontal overflow", async ({ page }) => {
    await completeTest(page);
    await page.locator("[data-result-detail='0']").click();
    await expect(page.getByTestId("proftest-detail-card")).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(overflow).toBe(false);
    await expect(page.getByTestId("proftest-restart")).toBeVisible();
  });

  test.describe("mobile viewport", () => {
    test.use({ viewport: { width: 390, height: 844 } });

    test("keeps cards and actions visible", async ({ page }) => {
      await completeTest(page);
      await expect(page.locator("[data-testid='result-card']").first()).toBeVisible();
      await page.locator("[data-result-detail='0']").click();
      await expect(page.getByTestId("proftest-detail-card")).toBeVisible();
      await expect(page.getByTestId("proftest-restart")).toBeVisible();
    });
  });
});
