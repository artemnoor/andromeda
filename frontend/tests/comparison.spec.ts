import { expect, test } from "@playwright/test";

test("user can select programmes and compare a semester", async ({ page }) => {
  await page.goto("/#compare");
  await expect(page.getByTestId("program-a")).toBeVisible();
  await page.getByTestId("comparison-scope").selectOption("semester");
  await page.getByTestId("comparison-semester").selectOption("1");
  await page.getByTestId("compare-submit").click();
  await expect(page.getByTestId("comparison-table")).toBeVisible();
  await expect(page.getByTestId("area-breakdown")).toBeVisible();
  await expect(page.getByText("Вектор содержания")).toBeVisible();
  await expect(page.getByText("Сопоставление дисциплин")).toBeVisible();
  await expect(page.locator(".status").first()).toBeVisible();
});
