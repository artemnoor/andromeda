import { expect, test, type Page } from "@playwright/test";

async function completeProfile(page: Page): Promise<void> {
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
}

test.describe("unified MVP flow", () => {
  test("shows the profile-required guide and keeps the proftest transition available", async ({ page }) => {
    await page.goto("/#flow");
    await expect(page.getByTestId("nav-unified-flow")).toHaveClass(/active/);
    await expect(page.getByTestId("unified-flow-page")).toBeVisible();
    await expect(page.getByTestId("unified-flow-stage")).toHaveCount(8);
    await expect(page.getByTestId("unified-flow-profile-required")).toBeVisible();

    await page.getByTestId("unified-flow-profile-required").getByRole("link", { name: "Открыть профтест" }).click();
    await expect(page).toHaveURL(/#proftest$/);
    await expect(page.getByTestId("proftest-start")).toBeVisible();
  });

  test("restores a completed profile and exposes recommendation, events and Personal Route transitions", async ({ page }) => {
    await completeProfile(page);
    await page.goto("/#flow");

    await expect(page.getByTestId("unified-flow-page")).toBeVisible();
    await expect(page.getByTestId("unified-flow-profile-status")).toContainText("Готово");
    await expect(page.getByTestId("unified-flow-recommendations-status")).toContainText("Готово");
    await expect(page.getByTestId("unified-flow-events-status")).toContainText("Готово");
    await expect(page.locator("[data-stage-id='program']").getByTestId("unified-flow-cta")).toHaveAttribute("href", /#program\/program%3A/);
    await expect(page.locator("[data-stage-id='admission-fit']").getByTestId("unified-flow-cta")).toHaveAttribute("href", /#program\/program%3A/);
    await expect(page.locator("[data-stage-id='events']").getByTestId("unified-flow-cta")).toHaveAttribute("href", "#events");
    await expect(page.locator("[data-stage-id='personal-route']").getByTestId("unified-flow-cta")).toHaveAttribute("href", "#personal-route");
  });
});

test.describe("unified MVP flow mobile", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("keeps ordered stages and CTA keyboard reachable on mobile", async ({ page }) => {
    await page.goto("/#flow");
    await expect(page.getByTestId("unified-flow-page")).toBeVisible();
    await expect(page.getByTestId("unified-flow-stage")).toHaveCount(8);
    const firstCta = page.getByTestId("unified-flow-cta").first();
    await firstCta.focus();
    await expect(firstCta).toBeFocused();
  });
});
