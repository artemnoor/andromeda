import { describe, expect, it } from "vitest";

import { renderEventsError } from "./EventsStates";

function fakeRoot(): HTMLElement {
  return { innerHTML: "" } as HTMLElement;
}

describe("event states", () => {
  it("escapes API error text before inserting it into the page", () => {
    const root = fakeRoot();

    renderEventsError(root, '<img src=x onerror="alert(1)"> & invalid');

    expect(root.innerHTML).not.toContain('<img src=x');
    expect(root.innerHTML).toContain("&lt;img src=x onerror=&quot;alert(1)&quot;&gt; &amp; invalid");
  });
});
