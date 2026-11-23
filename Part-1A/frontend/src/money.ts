// FR-022 / research R6: exact rupee-string -> paise parsing. Never uses floating point.
export const MAX_PAISE = 1_000_000_000;

export type ParseResult = { ok: true; paise: number } | { ok: false; error: string };

const VALID = /^(\d{1,8})(?:\.(\d{1,2}))?$/;
const TOO_MANY_DECIMALS = /^\d+\.\d{3,}$/;

export function parseRupees(input: string): ParseResult {
  const text = input.trim();
  if (text === "") return { ok: false, error: "Enter an amount" };
  if (TOO_MANY_DECIMALS.test(text)) return { ok: false, error: "Use at most 2 decimal places" };
  const match = VALID.exec(text);
  if (!match) return { ok: false, error: "Enter an amount like 1250 or 99.50" };
  const rupees = Number.parseInt(match[1], 10);
  const fraction = Number.parseInt((match[2] ?? "").padEnd(2, "0"), 10);
  const paise = rupees * 100 + fraction;
  if (paise < 1 || paise > MAX_PAISE) {
    return { ok: false, error: "Amount must be between ₹0.01 and ₹1,00,00,000.00" };
  }
  return { ok: true, paise };
}

function groupIndian(digits: string): string {
  if (digits.length <= 3) return digits;
  const last3 = digits.slice(-3);
  let rest = digits.slice(0, -3);
  const parts: string[] = [];
  while (rest.length > 2) {
    parts.unshift(rest.slice(-2));
    rest = rest.slice(0, -2);
  }
  if (rest) parts.unshift(rest);
  return `${parts.join(",")},${last3}`;
}

export function formatINR(paise: number): string {
  const sign = paise < 0 ? "-" : "";
  const abs = Math.abs(paise);
  const rupees = Math.floor(abs / 100);
  const fraction = String(abs % 100).padStart(2, "0");
  return `${sign}₹${groupIndian(String(rupees))}.${fraction}`;
}
