import { describe, expect, it } from "vitest";

import { count, moneyCompact, signedPercent } from "../lib/format";

describe("format", () => {
  it("compacts millions and thousands", () => {
    expect(moneyCompact(18_927_399)).toBe("£18.93m");
    expect(moneyCompact(-1_444_974)).toBe("−£1.44m");
    expect(moneyCompact(46_922)).toBe("£47k");
  });

  it("formats integer counts with separators", () => {
    expect(count(46922)).toBe("46,922");
  });

  it("signs percentages", () => {
    expect(signedPercent(2.33)).toBe("+2.3%");
    expect(signedPercent(-4.4)).toBe("-4.4%");
  });
});
