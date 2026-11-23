// T042 [US7] — FR-022 rupee input parsing (no floats) and FR-020 display formatting.
import { describe, expect, it } from "vitest";
import { formatINR, parseRupees } from "../src/money";

describe("FR-022 parseRupees", () => {
  it.each([
    ["1000", 100000],
    ["1000.5", 100050],
    ["1000.50", 100050],
    ["0.1", 10],
    ["0.01", 1],
    ["333.33", 33333],
    [" 42 ", 4200],
    ["10000000", 1_000_000_000],
  ])("parses %s -> %i paise", (input, paise) => {
    expect(parseRupees(input)).toEqual({ ok: true, paise });
  });

  it.each(["12.345", "abc", "-5", "1e3", "", "  ", "1,000", "0", "0.00", "10000000.01", ".5", "5."])(
    "rejects %s",
    (input) => {
      const r = parseRupees(input);
      expect(r.ok).toBe(false);
    },
  );

  it("gives a human readable reason for too many decimals", () => {
    const r = parseRupees("12.345");
    expect(r).toEqual({ ok: false, error: "Use at most 2 decimal places" });
  });
});

describe("FR-020 formatINR", () => {
  it.each([
    [0, "₹0.00"],
    [1, "₹0.01"],
    [33333, "₹333.33"],
    [100000, "₹1,000.00"],
    [10000000, "₹1,00,000.00"],
    [1_000_000_000, "₹1,00,00,000.00"],
    [-16667, "-₹166.67"],
  ])("formats %i -> %s", (paise, text) => {
    expect(formatINR(paise)).toBe(text);
  });
});
