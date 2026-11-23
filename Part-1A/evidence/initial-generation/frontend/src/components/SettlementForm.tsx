import { useState, type FormEvent } from "react";
import { api, today, type Member } from "../api";
import { parseRupees } from "../money";

type Props = { groupId: number; members: Member[]; onSaved: () => Promise<void> | void };

export default function SettlementForm({ groupId, members, onSaved }: Props) {
  const [from, setFrom] = useState(members[1]?.id ?? 0);
  const [to, setTo] = useState(members[0]?.id ?? 0);
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(today());
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (from === to) return setError("Payer and receiver must be different people");
    const parsed = parseRupees(amount);
    if (!parsed.ok) return setError(parsed.error);
    try {
      await api.addSettlement(groupId, { from_member: from, to_member: to, amount: parsed.paise, date });
      setAmount("");
      await onSaved();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <form className="card" onSubmit={submit} aria-labelledby="record-h">
      <h3 id="record-h">Record a payment</h3>
      <p className="muted small-text">Payments are permanent — to undo one, record it in reverse.</p>
      <div className="grid2">
        <label>
          From
          <select value={from} onChange={(e) => setFrom(Number.parseInt(e.target.value, 10))}>
            {members.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          To
          <select value={to} onChange={(e) => setTo(Number.parseInt(e.target.value, 10))}>
            {members.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Payment amount (₹)
          <input value={amount} onChange={(e) => setAmount(e.target.value)} inputMode="decimal" />
        </label>
        <label>
          Payment date
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </label>
      </div>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <button type="submit">Record payment</button>
    </form>
  );
}
