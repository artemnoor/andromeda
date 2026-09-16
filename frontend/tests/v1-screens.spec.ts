import { expect, test, type Page } from "@playwright/test";

async function completeProfile(page: Page): Promise<void> {
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

test.describe("Andromeda V1 journey", () => {
  test("moves from catalog to program, comparison, profile, recommendations, events, route and account", async ({ page }) => {
    await page.goto("/#catalog");
    await expect(page.getByTestId("catalog-page")).toBeVisible();
    await expect(page.getByTestId("catalog-program-link").first()).toBeVisible();

    await page.getByTestId("catalog-program-link").first().click();
    await expect(page).toHaveURL(/#program\/program%3A/);
    await expect(page.getByTestId("curriculum")).toBeVisible();
    await expect(page.getByTestId("admission-fit")).toBeVisible();

    await page.goto("/#compare");
    await expect(page.getByTestId("comparison-table")).toBeVisible();

    await completeProfile(page);

    await page.goto("/#recommendations");
    await expect(page.getByTestId("recommendations-results")).toBeVisible();
    await page.getByTestId("recommendation-program-link").first().click();
    await expect(page).toHaveURL(/#program\/program%3A/);
    await expect(page.getByTestId("admission-fit")).toBeVisible();

    const scores = page.locator("[data-testid='admission-fit'] input[data-admission-score]");
    for (let index = 0; index < await scores.count(); index += 1) await scores.nth(index).fill("90");
    await page.getByTestId("admission-fit-submit").click();
    await expect(page.getByTestId("admission-fit-success")).toBeVisible();

    await page.goto("/#events");
    await expect(page.getByTestId("events-results")).toBeVisible();
    await page.getByTestId("event-detail-link").first().click();
    await expect(page.getByTestId("event-detail")).toBeVisible();
    await expect(page.getByTestId("event-campus")).toBeVisible();
    await expect(page.getByTestId("event-campus-status")).toContainText("событий");

    await page.goto("/#personal-route");
    await expect(page.getByTestId("personal-route-results")).toBeVisible();
    await expect(page.getByTestId("personal-route-step").first()).toBeVisible();

    await page.goto("/#account");
    await expect(page.getByTestId("account-page")).toBeVisible();
    await expect(page.getByTestId("account-profile")).toContainText("Сохранённый профиль");
  });
});

test.describe("Andromeda V1 responsive routes", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("keeps every public and ops screen inside the mobile viewport", async ({ page }) => {
    const routes = [
      "#catalog",
      "#program/program%3A09.03.01-02",
      "#compare",
      "#proftest",
      "#recommendations",
      "#events",
      "#event/event%3Abmstu%3Adod-2026",
      "#personal-route",
      "#account",
      "#ops",
    ];

    for (const route of routes) {
      await page.goto(`/${route}`);
      await expect(page.locator("main").first()).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), route).toBe(true);
    }
  });
});
