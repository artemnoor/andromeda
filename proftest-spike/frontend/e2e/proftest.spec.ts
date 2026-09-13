import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";

import { expect, test } from "@playwright/test";

test.beforeAll(async () => {
  await mkdir(resolve(process.cwd(), "../output/playwright"), { recursive: true });
});

test("user completes the real curriculum proftest and opens explanation", async ({ page }, testInfo) => {
  await page.goto("/");
  await expect(page.getByTestId("intro-screen")).toBeVisible();
  await page.getByTestId("start-test").click();

  for (let step = 0; step < 6; step += 1) {
    await expect(page.getByTestId("question-screen")).toBeVisible();
    const option = page.locator("[data-testid^='question-option-']").first();
    if (step !== 5) await option.click();
    await page.getByTestId("next-button").click();
  }

  await expect(page.getByTestId("adaptive-screen")).toBeVisible();
  const adaptiveQuestion = page.locator("[data-testid^='adaptive-option-']");
  if (await adaptiveQuestion.count()) await adaptiveQuestion.first().click();
  await page.getByTestId("adaptive-next").click();
  await expect(page.getByTestId("results-screen")).toBeVisible();
  await expect(page.getByTestId("recommendation-card").first()).toBeVisible();
  await expect(page.getByTestId("reason-list").first()).toBeVisible();
  await page.screenshot({ path: `../output/playwright/${testInfo.project.name}-results.png`, fullPage: true });
  await page.getByTestId("open-detail").first().click();
  await expect(page.getByTestId("result-detail")).toBeVisible();
  await expect(page.getByTestId("optional-metrics")).toContainText("Пока недоступно");
  await page.screenshot({ path: `../output/playwright/${testInfo.project.name}-result-detail.png`, fullPage: true });
  await page.getByTestId("detail-back").click();
  await expect(page.getByTestId("results-screen")).toBeVisible();
  await page.reload();
  await expect(page.getByTestId("results-screen")).toBeVisible();
});

test("anti-interest control is selectable and keeps the mobile layout usable", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.getByTestId("start-test").click();
  for (let step = 0; step < 5; step += 1) {
    await page.locator("[data-testid^='question-option-']").first().click();
    await page.getByTestId("next-button").click();
  }
  await page.getByTestId("question-option-anti_physics").click();
  await expect(page.getByTestId("intensity-anti_physics")).toBeVisible();
  await page.getByTestId("next-button").click();
  await expect(page.getByTestId("adaptive-screen")).toBeVisible();
  const viewport = page.viewportSize();
  expect(viewport?.width).toBeGreaterThan(0);
  await page.screenshot({ path: `../output/playwright/${testInfo.project.name}-adaptive.png`, fullPage: true });
  await expect(page.getByTestId("adaptive-next")).toBeVisible();
});
