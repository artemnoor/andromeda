import { describe, expect, it } from "vitest";

import { filterCatalogPrograms } from "./CatalogPage";

const programs = [
  { id: "program:09.03.01-02", directionId: "direction:09.03.01", code: "09.03.01-02", name: "Информатика и вычислительная техника", educationYear: 2025, studyPlanUrl: "https://example.test/one.pdf", sourceUrl: "https://example.test/one" },
  { id: "program:15.03.06-01", directionId: "direction:15.03.06", code: "15.03.06-01", name: "Мехатроника и робототехника", educationYear: 2024, studyPlanUrl: "https://example.test/two.pdf", sourceUrl: "https://example.test/two" },
] as const;

describe("catalog filters", () => {
  it("searches by program name and narrows by year and direction", () => {
    expect(filterCatalogPrograms(programs, { search: "робот", year: "", direction: "" }).map((program) => program.id)).toEqual(["program:15.03.06-01"]);
    expect(filterCatalogPrograms(programs, { search: "", year: "2025", direction: "direction:15.03.06" })).toHaveLength(0);
    expect(filterCatalogPrograms(programs, { search: "", year: "2025", direction: "direction:09.03.01" })).toHaveLength(1);
  });
});
