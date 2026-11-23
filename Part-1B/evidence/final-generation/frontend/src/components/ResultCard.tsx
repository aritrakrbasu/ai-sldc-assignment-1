import type { ParseResult } from "../api";
import { formatINR, KIND_LABELS, REASON_LABELS, titleCase } from "../format";

const ERROR_LABELS: Record<string, string> = {
  DUPLICATE: "Already saved earlier (duplicate)",
  MESSAGE_TOO_LONG: "Message too long (over 1,000 characters)",
  MODEL_OUTPUT_INVALID: "AI output failed validation — not saved",
  MODEL_UNAVAILABLE: "AI service unavailable — try again",
};

export default function ResultCard({ result }: { result: ParseResult }) {
  const kind = result.kind ?? "ERROR";
  const t = result.transaction;
  const cls = result.status === "error" && result.error_code !== "DUPLICATE" ? "error-card" : kind.toLowerCase();
  return (
    <article className={`result ${cls}`}>
      <header>
        <span className={`badge ${kind.toLowerCase()}`}>{KIND_LABELS[kind] ?? "Error"}</span>
        {result.status === "error" && <span className="badge warn">{ERROR_LABELS[result.error_code ?? ""] ?? result.error_code}</span>}
      </header>
      {t && (
        <div className="txn">
          <span className={`amount ${t.direction === "DEBIT" ? "neg" : "pos"}`}>{formatINR(t.amount_paise)}</span>
          <span className="dir">{t.direction === "DEBIT" ? "debited" : "credited"}</span>
          <dl>
            <dt>Merchant</dt>
            <dd>{t.merchant ?? "—"}</dd>
            <dt>Category</dt>
            <dd>{titleCase(t.category)}</dd>
            <dt>Date</dt>
            <dd>{t.txn_date ?? "—"}</dd>
            <dt>Channel</dt>
            <dd>{t.channel}</dd>
            <dt>Account</dt>
            <dd>{t.account_last4 ? `••${t.account_last4}` : "—"}</dd>
          </dl>
        </div>
      )}
      {result.bill && (
        <dl>
          <dt>Biller</dt>
          <dd>{result.bill.biller ?? "—"}</dd>
          <dt>Amount due</dt>
          <dd>{formatINR(result.bill.amount_due_paise)}</dd>
          <dt>Due date</dt>
          <dd>{result.bill.due_date ?? "—"}</dd>
        </dl>
      )}
      {result.phishing && (
        <ul className="reasons" aria-label="Why this looks like phishing">
          {result.phishing.reasons.map((r) => (
            <li key={r}>{REASON_LABELS[r] ?? r}</li>
          ))}
        </ul>
      )}
      <p className="masked">{result.masked_text}</p>
    </article>
  );
}
