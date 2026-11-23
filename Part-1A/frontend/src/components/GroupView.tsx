import { useCallback, useEffect, useState } from "react";
import { api, type GroupDetail } from "../api";
import BalancesPanel from "./BalancesPanel";
import ExpenseForm from "./ExpenseForm";
import ExpenseList from "./ExpenseList";
import SettlementForm from "./SettlementForm";
import SettleUpPanel from "./SettleUpPanel";

export default function GroupView({ groupId, onBack }: { groupId: number; onBack: () => void }) {
  const [detail, setDetail] = useState<GroupDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  // US7-3: every mutation calls refresh() so panels update without a page reload.
  const refresh = useCallback(async () => {
    try {
      setDetail(await api.getGroup(groupId));
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, [groupId]);

  useEffect(() => {
    let alive = true;
    api
      .getGroup(groupId)
      .then((d) => alive && setDetail(d))
      .catch((e: Error) => alive && setError(e.message));
    return () => {
      alive = false;
    };
  }, [groupId]);

  if (error && !detail)
    return (
      <div className="card">
        <p role="alert" className="error">{error}</p>
        <button onClick={onBack}>← All groups</button>
      </div>
    );
  if (!detail) return <p className="muted">Loading…</p>;

  return (
    <div className="group-view">
      <div className="group-head">
        <button className="link" onClick={onBack}>
          ← All groups
        </button>
        <h2>{detail.name}</h2>
        <p className="muted">{detail.members.map((m) => m.name).join(" · ")}</p>
        <a className="button" href={api.exportUrl(groupId)} download>
          Export CSV
        </a>
      </div>
      <div className="columns">
        <div className="col">
          <ExpenseForm groupId={groupId} members={detail.members} onSaved={refresh} />
          <ExpenseList groupId={groupId} detail={detail} onChanged={refresh} />
        </div>
        <div className="col">
          <BalancesPanel balances={detail.balances} />
          <SettleUpPanel groupId={groupId} detail={detail} onRecorded={refresh} />
          <SettlementForm groupId={groupId} members={detail.members} onSaved={refresh} />
        </div>
      </div>
    </div>
  );
}
