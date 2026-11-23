import { useEffect, useState } from "react";
import GroupList from "./components/GroupList";
import GroupView from "./components/GroupView";

function parseRoute(hash: string): number | null {
  const m = /^#\/groups\/(\d+)$/.exec(hash);
  return m ? Number.parseInt(m[1], 10) : null;
}

export default function App() {
  const [groupId, setGroupId] = useState<number | null>(() => parseRoute(window.location.hash));

  useEffect(() => {
    const onHash = () => setGroupId(parseRoute(window.location.hash));
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const open = (id: number | null) => {
    window.location.hash = id === null ? "" : `#/groups/${id}`;
    setGroupId(id);
  };

  return (
    <div className="app">
      <header className="topbar">
        <button className="brand" onClick={() => open(null)} aria-label="Home">
          <span className="logo" aria-hidden="true">
            ₹
          </span>
        </button>
        <div>
          <h1>SplitEase</h1>
          <p className="tagline">Split shared expenses to the exact paisa.</p>
        </div>
      </header>
      <main>
        {groupId === null ? (
          <GroupList onOpen={open} />
        ) : (
          <GroupView key={groupId} groupId={groupId} onBack={() => open(null)} />
        )}
      </main>
    </div>
  );
}
