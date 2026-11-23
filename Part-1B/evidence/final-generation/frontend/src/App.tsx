import { useState } from "react";
import AskTab from "./components/AskTab";
import DashboardTab from "./components/DashboardTab";
import InboxTab from "./components/InboxTab";

const TABS = ["Inbox", "Dashboard", "Ask"] as const;
type Tab = (typeof TABS)[number];

export default function App() {
  const [tab, setTab] = useState<Tab>("Inbox");
  return (
    <div className="app">
      <header className="topbar">
        <span className="logo" aria-hidden="true">
          ML
        </span>
        <div>
          <h1>MoneyLens</h1>
          <p className="tagline">Your bank SMS, decoded — privately masked, never guessed.</p>
        </div>
      </header>
      <nav className="tabs" role="tablist" aria-label="Sections">
        {TABS.map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} className={tab === t ? "active" : ""} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </nav>
      <main>
        {tab === "Inbox" && <InboxTab />}
        {tab === "Dashboard" && <DashboardTab />}
        {tab === "Ask" && <AskTab />}
      </main>
    </div>
  );
}
