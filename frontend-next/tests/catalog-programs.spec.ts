import { expect, test, type Page } from "@playwright/test";

async function openCatalog(page: Page): Promise<void> {
  await page.goto("/?view=catalog");
  await expect(page.getByTestId("catalog-page")).toBeVisible();
  await expect(page.getByText(/Найдено программ:/)).toBeVisible();
}

test("catalog finishes loading and opens a source-backed program", async ({ page }) => {
  await openCatalog(page);
  await expect(page.getByRole("button", { name: "Открыть" }).first()).toBeVisible();
  await page.getByRole("button", { name: "Открыть", exact: true }).first().click();

  await expect(page.getByTestId("program-page")).toBeVisible();
  await expect(page.getByTestId("curriculum-table")).toBeVisible();
  await expect(page.getByText(/дисциплин/).first()).toBeVisible();

  await page.getByRole("tab", { name: "Поступление" }).click();
  await expect(page.getByTestId("admissions-section")).toBeVisible();
  await expect(page.getByText("Вступительные испытания").first()).toBeVisible();
});

test("comparison keeps category charts and legends available", async ({ page }) => {
  await openCatalog(page);
  const desktopCompare = page.getByTestId("nav-compare");
  if (await desktopCompare.isVisible().catch(() => false)) {
    await desktopCompare.click();
  } else {
    await page.getByTestId("mobile-nav-compare").click();
  }
  await expect(page.getByTestId("program-a")).toBeVisible();
  await expect(page.getByTestId("program-b")).toBeVisible();
  await expect(page.getByTestId("comparison-table")).toBeVisible();
  await expect(page.getByTestId("area-breakdown")).toBeVisible();
  await expect(page.getByTestId("area-pie-a")).toBeVisible();
  await expect(page.getByTestId("area-pie-b")).toBeVisible();
  await expect(page.getByTestId("area-pie-a").getByRole("list", { name: "Легенда программы A" })).toBeVisible();
  await expect(page.getByTestId("area-pie-b").getByRole("list", { name: "Легенда программы B" })).toBeVisible();
});
