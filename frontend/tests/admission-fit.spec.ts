import { expect, test, type Page } from "@playwright/test";

async function calculateAdmissionFit(page: Page): Promise<void> {
  await page.goto("/");
  await page.getByTestId("nav-program").click();
  await expect(page.getByTestId("admission-fit")).toBeVisible();
  const inputs = page.locator("[data-testid='admission-fit'] input[data-admission-score]");
  await expect(inputs.first()).toBeVisible();
  for (let index = 0; index < await inputs.count(); index += 1) {
    await inputs.nth(index).fill("90");
  }
  await page.getByTestId("admission-fit-submit").click();
  await expect(page.getByTestId("admission-fit-success")).toBeVisible();
}

test.describe("admission fit vertical slice", () => {
  test("calculates a separate fit from real admission requirements", async ({ page }) => {
    await calculateAdmissionFit(page);
    await expect(page.getByTestId("admission-fit-score")).toContainText("100");
    await expect(page.getByText("Что совпало")).toBeVisible();
    await expect(page.getByText("Каких данных не хватает")).toBeVisible();
    await expect(page.getByText("не влияет на Content Fit")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(false);
  });

  test.describe("mobile viewport", () => {
    test.use({ viewport: { width: 390, height: 844 } });

    test("keeps the form and explanation readable", async ({ page }) => {
      await calculateAdmissionFit(page);
      await expect(page.getByTestId("admission-fit-success")).toBeVisible();
      await expect(page.getByTestId("admission-fit-submit")).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(false);
    });
  });
});
