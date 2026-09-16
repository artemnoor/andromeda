import { expect, test } from "@playwright/test";

test("guest can start and complete the production proftest session", async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto("/?view=proftest");
  await expect(page.getByTestId("proftest-intro")).toBeVisible();
  await page.getByTestId("proftest-start").click();
  await expect(page.getByTestId("proftest-question")).toBeVisible();

  const question = page.getByTestId("proftest-question");
  const results = page.getByTestId("proftest-results");
  for (let step = 0; step < 48; step += 1) {
    if (await results.isVisible().catch(() => false)) break;
    const options = page.getByTestId("proftest-option");
    if (await options.count()) {
      await options.first().click();
    } else if (await page.getByRole("button", { name: "Пропустить" }).isVisible().catch(() => false)) {
      await page.getByRole("button", { name: "Пропустить" }).click();
    } else {
      await page.getByRole("button", { name: "Не уверен" }).click();
    }
    const next = page.getByTestId("proftest-next");
    await expect(next).toBeEnabled();
    const previousQuestionId = await question.getAttribute("data-question-id");
    await next.click();
    await expect.poll(async () => {
      if (await results.isVisible().catch(() => false)) return "results";
      const nextQuestionId = await question.getAttribute("data-question-id").catch(() => null);
      return nextQuestionId && nextQuestionId !== previousQuestionId ? nextQuestionId : "pending";
    }, { timeout: 30_000 }).not.toBe("pending");
  }

  await expect(results).toBeVisible();
  await expect(page.getByTestId("proftest-result-card").first()).toBeVisible();
});

test("proftest restores the current question after reload", async ({ page }) => {
  await page.goto("/?view=proftest");
  await page.getByTestId("proftest-start").click();
  await expect(page.getByTestId("proftest-question")).toBeVisible();
  await page.getByTestId("proftest-option").first().click();
  await page.reload();
  await expect(page.getByTestId("proftest-question")).toBeVisible();
  await expect(page.getByTestId("proftest-option").first()).toHaveAttribute("aria-pressed", "true");
});
