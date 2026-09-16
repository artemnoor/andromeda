import { expect, test, type Page } from "@playwright/test";

async function completeProfile(page: Page): Promise<void> {
  await page.goto("/");
  await page.getByTestId("nav-proftest").click();
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

async function openUnifiedFlow(page: Page): Promise<void> {
  await page.getByTestId("nav-unified-flow").click();
  await expect(page.getByTestId("unified-flow-page")).toBeVisible();
}

async function openFlowStage(page: Page, stageId: string): Promise<void> {
  await page.locator(`[data-stage-id='${stageId}']`).getByTestId("unified-flow-cta").click();
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

  test("follows the completed profile through the real module screens", async ({ page }) => {
    await completeProfile(page);
    await page.goto("/#flow");

    await expect(page.getByTestId("unified-flow-page")).toBeVisible();
    await expect(page.getByTestId("unified-flow-profile-status")).toContainText("Готово");
    await expect(page.getByTestId("unified-flow-recommendations-status")).toContainText("Готово");
    await expect(page.getByTestId("unified-flow-events-status")).toContainText("Готово");

    await openFlowStage(page, "recommendations");
    await expect(page).toHaveURL(/#proftest$/);
    await expect(page.getByTestId("proftest-results")).toBeVisible();
    await expect(page.locator("[data-testid='result-card']").first()).toBeVisible();

    await openUnifiedFlow(page);
    const programCta = page.locator("[data-stage-id='program']").getByTestId("unified-flow-cta");
    await expect(programCta).toHaveAttribute("href", /#program\/program%3A/);
    await programCta.click();
    await expect(page).toHaveURL(/#program\/program%3A/);
    await expect(page.getByText("Поступление и содержание")).toBeVisible();
    await expect(page.getByTestId("admission-fit")).toBeVisible();

    const admissionScores = page.locator("[data-testid='admission-fit'] input[data-admission-score]");
    for (let index = 0; index < await admissionScores.count(); index += 1) {
      await admissionScores.nth(index).fill("90");
    }
    await page.getByTestId("admission-fit-submit").click();
    await expect(page.getByTestId("admission-fit-success")).toBeVisible();

    await openUnifiedFlow(page);
    await openFlowStage(page, "compare");
    await expect(page).toHaveURL(/#compare$/);
    await expect(page.getByTestId("comparison-table")).toBeVisible();
    await expect(page.getByText("Сопоставление дисциплин")).toBeVisible();

    await openUnifiedFlow(page);
    await openFlowStage(page, "events");
    await expect(page).toHaveURL(/#events$/);
    await expect(page.getByTestId("events-results")).toBeVisible();
    await page.getByTestId("events-recommended").check();
    await page.getByTestId("events-apply").click();
    await expect(page.getByTestId("event-card")).toHaveCount(4);
    await expect(page.locator("[data-event-id='event:bmstu:research-day-2026']")).toHaveCount(0);

    await openUnifiedFlow(page);
    await openFlowStage(page, "personal-route");
    await expect(page).toHaveURL(/#personal-route$/);
    await expect(page.getByTestId("personal-route-results")).toBeVisible();
    await expect(page.getByTestId("personal-route-step").first()).toBeVisible();
  });
});

test.describe("unified MVP flow mobile", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("opens a real program screen and keeps CTA keyboard reachable on mobile", async ({ page }) => {
    await completeProfile(page);
    await page.goto("/#flow");
    await expect(page.getByTestId("unified-flow-page")).toBeVisible();
    await expect(page.getByTestId("unified-flow-stage")).toHaveCount(8);
    const programCta = page.locator("[data-stage-id='program']").getByTestId("unified-flow-cta");
    await programCta.focus();
    await expect(programCta).toBeFocused();
    await programCta.click();
    await expect(page.getByText("Поступление и содержание")).toBeVisible();
    await expect(page.getByTestId("admission-fit")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(false);
  });
});
