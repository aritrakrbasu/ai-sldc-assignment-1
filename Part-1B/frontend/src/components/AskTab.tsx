import { useState, type FormEvent } from "react";
import { api, type QueryResult } from "../api";
import { formatINR, titleCase } from "../format";

const EXAMPLES = ["How much did I spend on food last week?", "What's my biggest expense?", "How many times did I pay Swiggy this month?"];

export default function AskTab() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setBusy(true);
    setError(null);
    try {
      setResult(await api.ask(question.trim()));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const q = result?.query;
  const a = result?.answer;
  const headline =
    q && a ? (q.metric === "COUNT" ? `${a.count} transactions` : formatINR(a.value_paise)) : null;

  return (
    <div className="ask">
      <form className="card" onSubmit={submit}>
        <label htmlFor="question">Your question</label>
        <div className="row">
          <input id="question" value={question} onChange={(e) => setQuestion(e.target.value)} maxLength={300} placeholder="How much did I spend on food last week?" />
          <button className="primary" type="submit" disabled={busy}>
            Ask
          </button>
        </div>
        <div className="row examples">
          {EXAMPLES.map((ex) => (
            <button type="button" key={ex} className="chip" onClick={() => setQuestion(ex)}>
              {ex}
            </button>
          ))}
        </div>
      </form>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {result && result.status === "error" && (
        <p role="alert" className="error">
          {result.error_code === "MODEL_UNAVAILABLE" ? "The AI service is unavailable — try again." : "Could not interpret that question safely."}
        </p>
      )}
      {result && result.status === "ok" && result.intent !== "SPEND_QUERY" && (
        <section className="card">
          <p className="clarify">{result.clarification}</p>
        </section>
      )}
      {q && a && (
        <section className="card answer" aria-labelledby="answer-h">
          <h2 id="answer-h">Answer</h2>
          <p className="headline">{headline}</p>
          <p className="muted">
            {titleCase(q.metric)} of {q.direction === "DEBIT" ? "spending" : "money received"} · {a.count} transaction{a.count === 1 ? "" : "s"}
          </p>
          <div className="filters-used">
            <span>
              {q.date_from} → {q.date_to}
              {q.period_defaulted ? " (default: this month)" : ""}
            </span>
            <span>{q.categories.length ? q.categories.join(", ") : "All categories"}</span>
            {q.merchant_contains && <span>Merchant: {q.merchant_contains}</span>}
          </div>
          <p className="muted small">Figures are calculated by MoneyLens from your saved transactions, not by the AI.</p>
        </section>
      )}
    </div>
  );
}
