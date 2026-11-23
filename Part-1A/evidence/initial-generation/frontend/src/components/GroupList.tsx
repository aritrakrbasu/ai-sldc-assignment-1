import { useEffect, useState } from "react";
import { api, type GroupSummary } from "../api";
import CreateGroupForm from "./CreateGroupForm";

export default function GroupList({ onOpen }: { onOpen: (id: number) => void }) {
  const [groups, setGroups] = useState<GroupSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .listGroups()
      .then((g) => alive && setGroups(g))
      .catch((e: Error) => alive && setError(e.message));
    return () => {
      alive = false;
    };
  }, []);

  return (
    <div className="home">
      <section className="card" aria-labelledby="groups-h">
        <h2 id="groups-h">Your groups</h2>
        {error && <p role="alert" className="error">{error}</p>}
        {groups === null && !error && <p className="muted">Loading…</p>}
        {groups?.length === 0 && <p className="muted">No groups yet — create your first one.</p>}
        <ul className="group-list">
          {groups?.map((g) => (
            <li key={g.id}>
              <button className="group-item" onClick={() => onOpen(g.id)}>
                <span className="group-name">{g.name}</span>
                <span className="pill">{g.member_count} members</span>
              </button>
            </li>
          ))}
        </ul>
      </section>
      <CreateGroupForm onCreated={(g) => onOpen(g.id)} />
    </div>
  );
}
