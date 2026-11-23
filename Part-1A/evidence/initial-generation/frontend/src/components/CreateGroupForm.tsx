import { useState, type FormEvent } from "react";
import { api, type Group } from "../api";

export default function CreateGroupForm({ onCreated }: { onCreated: (g: Group) => void }) {
  const [name, setName] = useState("");
  const [members, setMembers] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const list = members
      .split("\n")
      .map((m) => m.trim())
      .filter(Boolean);
    if (!name.trim()) return setError("Give the group a name");
    if (list.length < 2) return setError("Add at least 2 members, one per line");
    setBusy(true);
    setError(null);
    try {
      onCreated(await api.createGroup(name.trim(), list));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card" onSubmit={submit} aria-labelledby="create-h">
      <h2 id="create-h">New group</h2>
      <label>
        Group name
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Goa trip" maxLength={60} />
      </label>
      <label>
        Members (one per line)
        <textarea
          value={members}
          onChange={(e) => setMembers(e.target.value)}
          rows={5}
          placeholder={"Asha\nBilal\nChen"}
        />
      </label>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <button type="submit" className="primary" disabled={busy}>
        Create group
      </button>
    </form>
  );
}
