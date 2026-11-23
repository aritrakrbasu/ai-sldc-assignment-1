import type { Balance } from "../api";
import { formatINR } from "../money";

export default function BalancesPanel({ balances }: { balances: Balance[] }) {
  return (
    <section className="card" aria-labelledby="balances-h">
      <h3 id="balances-h">Balances</h3>
      <ul className="balances">
        {balances.map((b) => (
          <li key={b.member_id}>
            <span>{b.name}</span>
            <span className={`tag ${b.balance > 0 ? "pos" : b.balance < 0 ? "neg" : "zero"}`}>
              {b.balance > 0 ? "gets back" : b.balance < 0 ? "owes" : "settled"}
            </span>
            <span className={`amount ${b.balance > 0 ? "pos" : b.balance < 0 ? "neg" : ""}`}>
              {formatINR(Math.abs(b.balance))}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
