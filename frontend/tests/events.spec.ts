import { expect, test, type Page } from "@playwright/test";

async function openEvents(page: Page): Promise<void> {
  await page.goto("/#events");
  await expect(page.getByTestId("nav-events")).toHaveClass(/active/);
  await expect(page.getByTestId("events-results")).toBeVisible();
}

async function completeProfile(page: Page): Promise<void> {
  await page.getByTestId("events-profile-link").click();
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
}

test.describe("events vertical slice", () => {
  test("renders event cards and applies type filters", async ({ page }) => {
    await openEvents(page);

    const cards = page.getByTestId("event-card");
    await expect(cards).toHaveCount(5);
    await expect(page.getByText("День открытых дверей ИУ")).toBeVisible();
    await expect(page.getByTestId("event-registration").first()).toHaveAttribute("href", /https:\/\/bmstu\.ru\/events\//);
    await expect(page.getByTestId("event-coordinates").first()).toContainText("55.7666");

    await page.getByTestId("events-kind").selectOption("additional_education");
    await page.getByTestId("events-apply").click();
    await expect(cards).toHaveCount(2);
    await expect(page.getByText("Практикум по робототехнике")).toBeVisible();
  });

  test("requires a profile and filters events by current recommendations", async ({ page }) => {
    await openEvents(page);
    await page.getByTestId("events-recommended").check();
    await page.getByTestId("events-apply").click();
    await expect(page.getByTestId("events-profile-required")).toBeVisible();

    await completeProfile(page);
    await page.goto("/#events");
    await expect(page.getByTestId("events-results")).toBeVisible();
    await page.getByTestId("events-recommended").check();
    await page.getByTestId("events-apply").click();

    await expect(page.getByTestId("event-card")).toHaveCount(4);
    await expect(page.locator("[data-event-id='event:bmstu:research-day-2026']")).toHaveCount(0);
  });
});
