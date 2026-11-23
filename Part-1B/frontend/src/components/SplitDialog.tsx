import { useEffect, useState } from "react";
import { api, type Member, type Txn } from "../api";
import { formatINR } from "../format";

type Props = { txn: Txn; onClose: () => void; onDone: (expenseId: number) => void };

export default function SplitDialog({ txn, onClose, onDone }: Props) {
  const [groups, setGroups] = useState<{ id: number; name: string }[]>([]);
  const [groupId, setGroupId] = useState<number | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [paidBy, setPaidBy] = useState<number | null>(null);
  const [chosen, setChosen] = useState<Record<number, boolean>>({});
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .groups()
      .then((g) => {
        if (!alive) return;
        setGroups(g);
        if (g[0]) setGroupId(g[0].id);
      })
      .catch((e: Error) => alive && setError(e.message));
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (groupId === null) return;
    let alive = true;
    api
      .group(groupId)
      .then((g) => {
        if (!alive) return;
        setMembers(g.members);
        setPaidBy(g.members[0]?.id ?? null);
        setChosen(Object.fromEntries(g.members.map((m) => [m.id, true])));
        setPreview(null);
      })
      .catch((e: Error) => alive && setError(e.message));
    return () => {
      alive = false;
    };
  }, [groupId]);

  const participants = members.filter((m) => chosen[m.id]).map((m) => m.id);

  async function send(confirm: boolean) {
    if (groupId === null || paidBy === null || participants.length === 0) return setError("Choose a group, payer and participants");
    setError(null);
    try {
      const res = await api.split(txn.id, { group_id: groupId, paid_by: paidBy, participants, confirm });
      if (res.status === "preview") {
        setPreview(`${res.payload.description} · ${formatINR(res.payload.amount)} · split equally between ${participants.length}`);
      } else {
        onDone(res.splitease_expense_id);
      }
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="overlay">
      <div className="card dialog" role="dialog" aria-modal="true" aria-labelledby="split-h">
        <h2 id="split-h">Split in SplitEase</h2>
        <p className="muted small">
          {txn.merchant ?? "Bank transaction"} · {formatINR(txn.amount_paise)} · {txn.txn_date ?? txn.reference_date}
        </p>
        <label>
          Group
          <select value={groupId ?? ""} onChange={(e) => setGroupId(Number.parseInt(e.target.value, 10))}>
            {groups.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Paid by
          <select value={paidBy ?? ""} onChange={(e) => setPaidBy(Number.parseInt(e.target.value, 10))}>
            {members.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </label>
        <fieldset>
          <legend>Split equally between</legend>
          {members.map((m) => (
            <label key={m.id} className="check">
              <input type="checkbox" checked={!!chosen[m.id]} onChange={(e) => setChosen({ ...chosen, [m.id]: e.target.checked })} />
              <span>{m.name}</span>
            </label>
          ))}
        </fieldset>
        {preview && <p className="preview">{preview}</p>}
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <div className="row">
          <button onClick={onClose}>Cancel</button>
          {preview ? (
            <button className="primary" onClick={() => send(true)}>
              Confirm and send
            </button>
          ) : (
            <button className="primary" onClick={() => send(false)}>
              Preview
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
