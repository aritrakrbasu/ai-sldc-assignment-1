import { useState } from "react";
import { api, today, type GroupDetail } from "../api";
import { formatINR } from "../money";

type Props = { groupId: number; detail: GroupDetail; onRecorded: () => Promise<void> | void };

export default function SettleUpPanel({ groupId, detail, onRecorded }: Props) {
  const [error, setError] = useState<string | null>(null);
  const name = (id: number) => detail.members.find((m) => m.id === id)?.name ?? "?";

  async function record(from: number, to: number, amount: number) {
    try {
      await api.addSettlement(groupId, { from_member: from, to_member: to, amount, date: today() });
      await onRecorded();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <section className="card" aria-labelledby="settle-h">
      <h3 id="settle-h">Settle up</h3>
      {error && <p role="alert" className="error">{error}</p>}
      {detail.settle_up.length === 0 ? (
        <p className="muted">Everyone is settled up. 🎉</p>
      ) : (
        <ul className="payments">
          {detail.settle_up.map((p) => (
            <li key={`${p.from_member}-${p.to_member}`}>
              <span>
                {name(p.from_member)} pays {name(p.to_member)} {formatINR(p.amount)}
              </span>
              <button onClick={() => record(p.from_member, p.to_member, p.amount)}>Record</button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
