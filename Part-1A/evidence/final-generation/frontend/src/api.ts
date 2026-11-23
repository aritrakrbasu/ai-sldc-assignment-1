// Typed client for contracts/api.md (C1-C9).
export type Member = { id: number; name: string; position: number };
export type Group = { id: number; name: string; members: Member[] };
export type GroupSummary = { id: number; name: string; member_count: number };
export type SplitMode = "EQUAL" | "EXACT" | "PERCENT" | "SHARES";
export type SplitIn = { member_id: number; amount?: number; percent?: string; weight?: number };
export type Expense = {
  id: number;
  description: string;
  amount: number;
  paid_by: number;
  date: string;
  split_mode: SplitMode;
  splits: SplitIn[];
  shares: { member_id: number; amount: number }[];
};
export type Settlement = { id: number; from_member: number; to_member: number; amount: number; date: string };
export type Balance = { member_id: number; name: string; balance: number };
export type Payment = { from_member: number; to_member: number; amount: number };
export type GroupDetail = Group & {
  expenses: Expense[];
  settlements: Settlement[];
  balances: Balance[];
  settle_up: Payment[];
};
export type ExpenseIn = {
  description: string;
  amount: number;
  paid_by: number;
  date: string;
  split_mode: SplitMode;
  splits: SplitIn[];
};
export type SettlementIn = { from_member: number; to_member: number; amount: number; date: string };

export class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  const init: RequestInit = { method };
  if (body !== undefined) {
    init.headers = { "Content-Type": "application/json" };
    init.body = JSON.stringify(body);
  }
  const res = await fetch(path, init);
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = data?.error;
    throw new ApiError(err?.message ?? `Request failed (${res.status})`, err?.code ?? "HTTP_ERROR");
  }
  return data as T;
}

export const api = {
  listGroups: () => request<GroupSummary[]>("/api/groups"),
  createGroup: (name: string, members: string[]) =>
    request<Group>("/api/groups", "POST", { name, members }),
  getGroup: (id: number) => request<GroupDetail>(`/api/groups/${id}`),
  addExpense: (id: number, body: ExpenseIn) => request<Expense>(`/api/groups/${id}/expenses`, "POST", body),
  deleteExpense: (id: number, eid: number) => request<void>(`/api/groups/${id}/expenses/${eid}`, "DELETE"),
  addSettlement: (id: number, body: SettlementIn) =>
    request<Settlement>(`/api/groups/${id}/settlements`, "POST", body),
  exportUrl: (id: number) => `/api/groups/${id}/export.csv`,
};

export function today(): string {
  const d = new Date();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
}
