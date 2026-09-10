import { expect, test, type Page } from "@playwright/test";

async function completeProftest(page: Page): Promise<void> {
  await page.goto("/");
  await page.getByTestId("nav-proftest").click();
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
  await expect(page.locator("[data-testid='result-card']").first()).toBeVisible();
  await page.locator("[data-result-detail='0']").click();
  await expect(page.getByTestId("proftest-detail-card")).toBeVisible();
  await expect(page.getByText("Почему подходит")).toBeVisible();
}

test("user can complete proftest and inspect an explainable recommendation", async ({ page }) => {
  await completeProftest(page);
  await expect(page.locator(".fit-score")).toBeVisible();
});

test("restores the current question after reload", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("nav-proftest").click();
  await page.getByTestId("proftest-start").click();
  await page.locator(".choice-card").first().click();
  await page.reload();
  await expect(page.getByTestId("proftest-progress")).toHaveText("1 / 6");
  await expect(page.locator(".choice-card.selected")).toHaveCount(1);
});

test.describe("mobile proftest", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("keeps question and result layout readable on a mobile viewport", async ({ page }) => {
    await completeProftest(page);
    await expect(page.getByTestId("proftest-detail-card")).toBeVisible();
    await expect(page.locator(".app-nav")).toBeVisible();
  });
});
