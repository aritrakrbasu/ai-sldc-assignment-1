// Display helpers. Money arrives as integer paise; never parsed from floats.
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

export function formatINR(paise: number | null | undefined): string {
  if (paise === null || paise === undefined) return "—";
  const sign = paise < 0 ? "-" : "";
  const abs = Math.abs(paise);
  return `${sign}₹${groupIndian(String(Math.floor(abs / 100)))}.${String(abs % 100).padStart(2, "0")}`;
}

// US6-1: messages are separated by one or more blank lines.
export function splitMessages(text: string): string[] {
  return text
    .replace(/\r\n/g, "\n")
    .split(/\n\s*\n/)
    .map((m) => m.trim())
    .filter(Boolean);
}

export const REASON_LABELS: Record<string, string> = {
  SUSPICIOUS_LINK: "Suspicious link",
  URGENCY_THREAT: "Urgency or threat",
  ASKS_FOR_CREDENTIALS: "Asks for credentials",
  KYC_UPDATE_LURE: "KYC update lure",
  PRIZE_OR_LOTTERY: "Prize or lottery",
  IMPERSONATION: "Impersonation",
  PROMPT_INJECTION: "Embedded instructions",
  OTHER: "Other",
};

export const KIND_LABELS: Record<string, string> = {
  TRANSACTION: "Transaction",
  OTP: "OTP (masked)",
  PROMOTION: "Promotion",
  BILL_REMINDER: "Bill reminder",
  PHISHING_SUSPECT: "Suspected phishing",
  OTHER: "Other",
};

export function titleCase(s: string): string {
  return s
    .toLowerCase()
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}
