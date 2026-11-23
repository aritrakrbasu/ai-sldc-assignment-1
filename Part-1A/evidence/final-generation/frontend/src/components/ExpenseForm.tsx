import { useState, type FormEvent } from "react";
import { api, today, type Member, type SplitIn, type SplitMode } from "../api";
import { parseRupees } from "../money";

const MODES: { value: SplitMode; label: string }[] = [
  { value: "EQUAL", label: "Equally" },
  { value: "EXACT", label: "Exact amounts" },
  { value: "PERCENT", label: "Percentages" },
  { value: "SHARES", label: "Shares" },
];

type Props = { groupId: number; members: Member[]; onSaved: () => Promise<void> | void };

export default function ExpenseForm({ groupId, members, onSaved }: Props) {
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [paidBy, setPaidBy] = useState(members[0]?.id ?? 0);
  const [date, setDate] = useState(today());
  const [mode, setMode] = useState<SplitMode>("EQUAL");
  const [included, setIncluded] = useState<Record<number, boolean>>(
    Object.fromEntries(members.map((m) => [m.id, true])),
  );
  const [values, setValues] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function buildSplits(): SplitIn[] | string {
    const chosen = members.filter((m) => included[m.id]);
    if (chosen.length === 0) return "Choose at least one person";
    if (mode === "EQUAL") return chosen.map((m) => ({ member_id: m.id }));
    const out: SplitIn[] = [];
    for (const m of chosen) {
      const raw = (values[m.id] ?? "").trim();
      if (mode === "EXACT") {
        if (raw === "" || raw === "0") {
          out.push({ member_id: m.id, amount: 0 });
          continue;
        }
        const p = parseRupees(raw);
        if (!p.ok) return `${m.name}: ${p.error}`;
        out.push({ member_id: m.id, amount: p.paise });
      } else if (mode === "PERCENT") {
        if (!/^\d{1,3}(\.\d{1,2})?$/.test(raw)) return `${m.name}: enter a percentage like 33.33`;
        out.push({ member_id: m.id, percent: raw });
      } else {
        if (!/^\d+$/.test(raw) || Number.parseInt(raw, 10) < 1) return `${m.name}: shares must be a whole number ≥ 1`;
        out.push({ member_id: m.id, weight: Number.parseInt(raw, 10) });
      }
    }
    return out;
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!description.trim()) return setError("Add a description");
    const parsed = parseRupees(amount);
    if (!parsed.ok) return setError(parsed.error);
    const splits = buildSplits();
    if (typeof splits === "string") return setError(splits);
    setBusy(true);
    try {
      await api.addExpense(groupId, {
        description: description.trim(),
        amount: parsed.paise,
        paid_by: paidBy,
        date,
        split_mode: mode,
        splits,
      });
      setDescription("");
      setAmount("");
      setValues({});
      await onSaved();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const valueLabel = mode === "EXACT" ? "Amount for" : mode === "PERCENT" ? "Percent for" : "Shares for";

  return (
    <form className="card" onSubmit={submit} aria-labelledby="add-exp-h">
      <h3 id="add-exp-h">Add expense</h3>
      <div className="grid2">
        <label>
          Description
          <input value={description} onChange={(e) => setDescription(e.target.value)} maxLength={120} />
        </label>
        <label>
          Amount (₹)
          <input value={amount} onChange={(e) => setAmount(e.target.value)} inputMode="decimal" placeholder="0.00" />
        </label>
        <label>
          Paid by
          <select value={paidBy} onChange={(e) => setPaidBy(Number.parseInt(e.target.value, 10))}>
            {members.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Date
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </label>
      </div>
      <fieldset className="modes">
        <legend>Split</legend>
        {MODES.map((m) => (
          <label key={m.value} className={`chip ${mode === m.value ? "active" : ""}`}>
            <input
              type="radio"
              name="split-mode"
              value={m.value}
              checked={mode === m.value}
              onChange={() => setMode(m.value)}
            />
            {m.label}
          </label>
        ))}
      </fieldset>
      <ul className="participants">
        {members.map((m) => (
          <li key={m.id}>
            <label className="check">
              <input
                type="checkbox"
                checked={!!included[m.id]}
                onChange={(e) => setIncluded({ ...included, [m.id]: e.target.checked })}
              />
              {m.name}
            </label>
            {mode !== "EQUAL" && included[m.id] && (
              <input
                aria-label={`${valueLabel} ${m.name}`}
                className="small"
                value={values[m.id] ?? ""}
                onChange={(e) => setValues({ ...values, [m.id]: e.target.value })}
                placeholder={mode === "EXACT" ? "₹" : mode === "PERCENT" ? "%" : "1"}
              />
            )}
          </li>
        ))}
      </ul>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <button type="submit" className="primary" disabled={busy}>
        Add expense
      </button>
    </form>
  );
}
