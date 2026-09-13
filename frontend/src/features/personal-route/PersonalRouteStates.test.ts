import { describe, expect, it } from "vitest";

import { renderPersonalRouteError, renderPersonalRouteProfileRequired } from "./PersonalRouteStates";

function fakeRoot(): HTMLElement {
  return { innerHTML: "" } as HTMLElement;
}

describe("personal route states", () => {
  it("escapes API errors", () => {
    const root = fakeRoot();

    renderPersonalRouteError(root, '<img src=x onerror="alert(1)">');

    expect(root.innerHTML).not.toContain("<img src=x");
    expect(root.innerHTML).toContain("&lt;img src=x onerror=&quot;alert(1)&quot;&gt;");
  });

  it("offers the profile flow when the current profile is absent", () => {
    const root = fakeRoot();

    renderPersonalRouteProfileRequired(root);

    expect(root.innerHTML).toContain('data-testid="personal-route-profile-link"');
    expect(root.innerHTML).toContain('href="#proftest"');
  });
});
