import { useState } from "react";
import { api, type GroupDetail } from "../api";
import { formatINR } from "../money";

type Props = { groupId: number; detail: GroupDetail; onChanged: () => Promise<void> | void };

export default function ExpenseList({ groupId, detail, onChanged }: Props) {
  const [error, setError] = useState<string | null>(null);
  const name = (id: number) => detail.members.find((m) => m.id === id)?.name ?? "?";

  type Row =
    | { kind: "expense"; id: number; date: string; text: string; who: string; amount: number }
    | { kind: "settlement"; id: number; date: string; text: string; who: string; amount: number };
  const rows: Row[] = [
    ...detail.expenses.map((e) => ({
      kind: "expense" as const,
      id: e.id,
      date: e.date,
      text: e.description,
      who: `${name(e.paid_by)} paid · ${e.split_mode.toLowerCase()}`,
      amount: e.amount,
    })),
    ...detail.settlements.map((s) => ({
      kind: "settlement" as const,
      id: s.id,
      date: s.date,
      text: `${name(s.from_member)} paid ${name(s.to_member)}`,
      who: "settlement",
      amount: s.amount,
    })),
  ].sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0));

  async function remove(id: number) {
    try {
      await api.deleteExpense(groupId, id);
      await onChanged();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <section className="card" aria-labelledby="ledger-h">
      <h3 id="ledger-h">Activity</h3>
      {error && <p role="alert" className="error">{error}</p>}
      {rows.length === 0 && <p className="muted">Nothing recorded yet.</p>}
      <ul className="ledger">
        {rows.map((r) => (
          <li key={`${r.kind}-${r.id}`} className={r.kind}>
            <div>
              <span className="ledger-title">{r.text}</span>
              <span className="muted small-text">
                {r.date} · {r.who}
              </span>
            </div>
            <span className="amount">{formatINR(r.amount)}</span>
            {r.kind === "expense" ? (
              <button className="icon" aria-label={`Delete ${r.text}`} onClick={() => remove(r.id)}>
                ✕
              </button>
            ) : (
              <span className="icon-spacer" />
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
