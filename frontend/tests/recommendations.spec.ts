import { expect, test, type Page } from "@playwright/test";

async function completeTest(page: Page): Promise<void> {
  await page.goto("/#proftest");
  await expect(page.getByTestId("proftest-start")).toBeVisible();
  await page.getByTestId("proftest-start").click();
  for (let index = 0; index < 6; index += 1) {
    await expect(page.getByTestId("proftest-progress")).toContainText(`${index + 1} / 6`);
    await page.locator(".choice-card").first().click();
    await page.getByTestId("proftest-next").click();
  }
  await page.waitForSelector("[data-testid='adaptive-submit'], [data-testid='adaptive-skipped-continue']", { state: "visible" });
  const adaptive = page.locator("[data-testid='adaptive-submit']");
  if (await adaptive.isVisible().catch(() => false)) {
    await page.locator("[data-adaptive-option]").first().click();
    await adaptive.click();
  } else {
    await page.getByTestId("adaptive-skipped-continue").click();
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
    await expect(page.getByText("Блоки дисциплин")).toBeVisible();
    await expect(page.getByText("Семестры")).toBeVisible();
    await expect(page.getByText(/Workload readiness/)).toBeVisible();
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
