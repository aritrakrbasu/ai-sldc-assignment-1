// T038 [US6] — formatting and message splitting.
import { describe, expect, it } from "vitest";
import { formatINR, splitMessages } from "../src/format";

describe("formatINR", () => {
  it.each([
    [0, "₹0.00"],
    [25000, "₹250.00"],
    [8534900, "₹85,349.00"],
    [23500000, "₹2,35,000.00"],
    [null, "—"],
  ])("%s -> %s", (paise, text) => {
    expect(formatINR(paise)).toBe(text);
  });
});

describe("splitMessages (US6-1)", () => {
  it("splits on blank lines and trims", () => {
    expect(splitMessages("first sms\nline two\n\n  second sms  \n\n\n\nthird")).toEqual([
      "first sms\nline two",
      "second sms",
      "third",
    ]);
  });
  it("handles CRLF from uploaded .txt files and ignores empty input", () => {
    expect(splitMessages("a\r\n\r\nb\r\n")).toEqual(["a", "b"]);
    expect(splitMessages("   \n\n ")).toEqual([]);
  });
});
