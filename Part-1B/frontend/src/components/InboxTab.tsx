import { useState, type ChangeEvent } from "react";
import { api, type ParseResult } from "../api";
import { splitMessages } from "../format";
import ResultCard from "./ResultCard";

const SAMPLE = `Rs.250.00 debited from A/c XX4821 on 18-11-26 to VPA swiggy@icici (UPI Ref 432198765012).

482913 is your OTP for login to SBI YONO. Do not share it with anyone.

Dear customer your SBI KYC expires today, update now at http://bit.ly/x9 or account will be blocked`;

export default function InboxTab() {
  const [text, setText] = useState("");
  const [results, setResults] = useState<ParseResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run() {
    const messages = splitMessages(text);
    if (messages.length === 0) return setError("Paste at least one message");
    if (messages.length > 50) return setError("At most 50 messages at a time");
    setError(null);
    setBusy(true);
    try {
      setResults((await api.parse(messages)).results);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function upload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) setText(await file.text());
  }

  const counts = results?.reduce<Record<string, number>>((acc, r) => {
    const k = r.status === "error" ? r.error_code ?? "ERROR" : r.kind ?? "OTHER";
    acc[k] = (acc[k] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="inbox">
      <section className="card" aria-labelledby="paste-h">
        <h2 id="paste-h">Paste your bank & UPI SMS</h2>
        <p className="muted small">
          Separate messages with a blank line. OTPs and long card/account numbers are masked on this server before anything
          is sent to the AI.
        </p>
        <label className="sr" htmlFor="sms-box">
          Paste SMS messages
        </label>
        <textarea id="sms-box" rows={9} value={text} onChange={(e) => setText(e.target.value)} placeholder="Rs.250.00 debited from A/c XX4821 ..." />
        <div className="row">
          <button className="primary" onClick={run} disabled={busy}>
            {busy ? "Parsing…" : "Parse messages"}
          </button>
          <label className="button file">
            Upload .txt
            <input type="file" accept=".txt,text/plain" onChange={upload} />
          </label>
          <button className="link" onClick={() => setText(SAMPLE)}>
            Try sample messages
          </button>
        </div>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
      </section>
      {results && (
        <section aria-labelledby="results-h">
          <h2 id="results-h">Results</h2>
          <p className="muted small">
            {Object.entries(counts ?? {})
              .map(([k, v]) => `${v} ${k.toLowerCase().replace(/_/g, " ")}`)
              .join(" · ")}
          </p>
          <div className="cards">
            {results.map((r) => (
              <ResultCard key={r.index} result={r} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
