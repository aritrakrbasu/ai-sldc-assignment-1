import { useCallback, useEffect, useState } from "react";
import { api, type Dashboard, type Txn } from "../api";
import { formatINR, titleCase } from "../format";
import SplitDialog from "./SplitDialog";

export default function DashboardTab() {
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [splitting, setSplitting] = useState<Txn | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async (f?: string, t?: string) => {
    try {
      setData(await api.dashboard(f || undefined, t || undefined));
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    let alive = true;
    api
      .dashboard()
      .then((d) => alive && setData(d))
      .catch((e: Error) => alive && setError(e.message));
    return () => {
      alive = false;
    };
  }, []);

  const max = Math.max(1, ...(data?.by_category.map((c) => c.value_paise) ?? [1]));

  return (
    <div className="dashboard">
      <section className="card filters" aria-label="Period">
        <label>
          From
          <input type="date" value={from || data?.from || ""} onChange={(e) => setFrom(e.target.value)} />
        </label>
        <label>
          To
          <input type="date" value={to || data?.to || ""} onChange={(e) => setTo(e.target.value)} />
        </label>
        <button onClick={() => load(from || data?.from, to || data?.to)}>Apply</button>
      </section>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {notice && <p className="notice">{notice}</p>}
      {data && (
        <div className="grid">
          <section className="card" aria-labelledby="spend-h">
            <h2 id="spend-h">Spend by category</h2>
            <div className="totals">
              <div>
                <span className="muted small">Spent</span>
                <strong className="neg">{formatINR(data.total_debit_paise)}</strong>
              </div>
              <div>
                <span className="muted small">Received</span>
                <strong className="pos">{formatINR(data.total_credit_paise)}</strong>
              </div>
            </div>
            {data.by_category.length === 0 && <p className="muted">No spending in this period.</p>}
            <ul className="bars">
              {data.by_category.map((c) => (
                <li key={c.category}>
                  <span className="bar-label">{titleCase(c.category)}</span>
                  <span className="bar">
                    <span style={{ width: `${(c.value_paise / max) * 100}%` }} />
                  </span>
                  <span className="bar-value">{formatINR(c.value_paise)}</span>
                </li>
              ))}
            </ul>
          </section>
          <section className="card" aria-labelledby="recent-h">
            <h2 id="recent-h">Recent transactions</h2>
            {data.recent.length === 0 && <p className="muted">Parse some SMS in the Inbox to see them here.</p>}
            <ul className="recent">
              {data.recent.map((t) => (
                <li key={t.id}>
                  <div>
                    <span className="recent-title">{t.merchant ?? "Bank transaction"}</span>
                    <span className="muted small">
                      {t.txn_date ?? t.reference_date} · {titleCase(t.category)}
                    </span>
                  </div>
                  <span className={`amount ${t.direction === "DEBIT" ? "neg" : "pos"}`}>
                    {t.direction === "DEBIT" ? "−" : "+"}
                    {formatINR(t.amount_paise)}
                  </span>
                  {t.direction === "DEBIT" &&
                    (t.shared_expense_id ? (
                      <span className="pill">shared</span>
                    ) : (
                      <button aria-label={`Split ${t.merchant ?? "transaction"} in SplitEase`} onClick={() => setSplitting(t)}>
                        Split
                      </button>
                    ))}
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
      {splitting && (
        <SplitDialog
          txn={splitting}
          onClose={() => setSplitting(null)}
          onDone={(id) => {
            setSplitting(null);
            setNotice(`Sent to SplitEase (expense #${id}).`);
            void load(from || data?.from, to || data?.to);
          }}
        />
      )}
    </div>
  );
}
