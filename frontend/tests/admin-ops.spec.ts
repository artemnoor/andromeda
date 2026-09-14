import { expect, test } from "@playwright/test";

const opsKey = process.env.ANDROMEDA_OPS_API_KEY;

test.describe("admin ops vertical slice", () => {
  test.skip(!opsKey, "ANDROMEDA_OPS_API_KEY is required for the protected operator browser check");

  test("loads audit detail and confirms a bounded fixture retry", async ({ page }) => {
    await page.goto("/#ops");
    await expect(page.getByTestId("ops-page")).toBeVisible();
    await page.getByTestId("ops-key").fill(opsKey ?? "");
    await page.getByTestId("ops-connect").click();

    await expect(page.getByTestId("ops-run-row").first()).toBeVisible();
    await expect(page.getByTestId("ops-detail")).toContainText("Источники");
    await expect(page.getByTestId("ops-detail")).toContainText("Конфликты и неразобранные записи");

    let confirmationSeen = false;
    page.on("dialog", async (dialog) => {
      confirmationSeen = true;
      await dialog.accept();
    });
    await page.getByTestId("ops-retry").click();
    await expect.poll(() => page.getByTestId("ops-run-row").count(), { timeout: 30_000 }).toBeGreaterThan(1);
    expect(confirmationSeen).toBe(true);
  });

  test("does not reveal the operator screen with a wrong key", async ({ page }) => {
    await page.goto("/#ops");
    await page.getByTestId("ops-key").fill("wrong-key");
    await page.getByTestId("ops-connect").click();
    await expect(page.getByTestId("ops-error-state")).toContainText("Доступ");
    await expect(page.getByTestId("ops-run-row")).toHaveCount(0);
  });
});
