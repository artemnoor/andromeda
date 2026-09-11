import { expect, test } from "@playwright/test";

test("user can open a programme and inspect source-backed admissions", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("nav-program").click();
  await expect(page.getByTestId("program-detail-select")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Поступление", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "ЕГЭ и минимумы" }).first()).toBeVisible();
  await expect(page.getByText("318", { exact: true })).toBeVisible();
  await expect(page.getByText("529 000", { exact: false })).toBeVisible();

  await page.getByTestId("program-detail-select").selectOption("program:09.03.01-12");
  await expect(page).toHaveURL(/#program\/program%3A09\.03\.01-12/);
  await expect(page.getByRole("heading", { name: "Поступление", exact: true })).toBeVisible();
  await expect(page.getByText("По направлению", { exact: true }).first()).toBeVisible();
});
