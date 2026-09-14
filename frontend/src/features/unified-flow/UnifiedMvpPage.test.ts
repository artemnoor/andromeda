import { describe, expect, it } from "vitest";

import { renderUnifiedMvpMarkup } from "./UnifiedMvpPage";
import type { UnifiedReadModel } from "./unifiedMvpState";

const readyModel: UnifiedReadModel = {
  profile: { status: "ready" },
  recommendations: { status: "ready", count: 2, firstProgramId: "program:09.03.01-02" },
  events: { status: "ready", count: 3 },
};

describe("UnifiedMvpPage markup", () => {
  it("renders all ordered stages and existing hash CTAs for ready data", () => {
    const markup = renderUnifiedMvpMarkup(readyModel, [{ id: "program:09.03.01-02", code: "09.03.01-02", name: "Информатика и вычислительная техника" } as never]);

    expect(markup).toContain('data-testid="unified-flow-page"');
    expect(markup.match(/data-testid="unified-flow-stage"/g)).toHaveLength(8);
    expect(markup).toContain('href="#program/program%3A09.03.01-02"');
    expect(markup).toContain('href="#compare"');
    expect(markup).toContain('href="#proftest"');
    expect(markup).toContain('href="#events"');
    expect(markup).toContain('href="#personal-route"');
    expect(markup).toContain("Информатика и вычислительная техника");
  });

  it("renders profile-required state without copying subject content", () => {
    const markup = renderUnifiedMvpMarkup({
      profile: { status: "profile-required" },
      recommendations: { status: "profile-required", count: 0 },
      events: { status: "profile-required", count: 0 },
    }, []);

    expect(markup).toContain('data-testid="unified-flow-profile-required"');
    expect(markup).toContain("Нужен профиль");
    expect(markup).toContain('href="#proftest"');
    expect(markup).not.toContain("Content Fit");
    expect(markup).not.toContain("event-card");
    expect(markup).not.toContain("admission-fit-form");
  });

  it("renders empty and partial-error states while preserving navigation", () => {
    const markup = renderUnifiedMvpMarkup({
      profile: { status: "ready" },
      recommendations: { status: "empty", count: 0 },
      events: { status: "error", count: 0 },
    }, []);

    expect(markup).toContain('data-testid="unified-flow-read-warning"');
    expect(markup).toContain("Пока пусто");
    expect(markup).toContain("Не удалось проверить");
    expect(markup).toContain('href="#events"');
    expect(markup).toContain('href="#personal-route"');
  });

  it("escapes program labels rendered in the guide", () => {
    const markup = renderUnifiedMvpMarkup({
      ...readyModel,
      recommendations: { status: "ready", count: 1, firstProgramId: "<script>alert(1)</script>" },
    }, []);

    expect(markup).toContain("&lt;script&gt;alert(1)&lt;/script&gt;");
    expect(markup).not.toContain("<script>alert(1)</script>");
  });
});
