// Typed client for contracts/api.md (M1-M8).
export type Txn = {
  id: number;
  amount_paise: number;
  direction: "DEBIT" | "CREDIT";
  merchant: string | null;
  account_last4: string | null;
  txn_date: string | null;
  channel: string;
  category: string;
  shared_expense_id: number | null;
  masked_text: string;
  reference_date: string;
};
export type ParseResult = {
  index: number;
  status: "ok" | "error";
  error_code: string | null;
  masked_text: string;
  kind: string | null;
  transaction: Omit<Txn, "id" | "shared_expense_id" | "masked_text" | "reference_date"> | null;
  bill: { amount_due_paise: number | null; due_date: string | null; biller: string | null } | null;
  phishing: { reasons: string[] } | null;
};
export type Query = {
  metric: string;
  direction: string;
  categories: string[];
  merchant_contains: string | null;
  date_from: string;
  date_to: string;
  period_defaulted: boolean;
};
export type QueryResult = {
  status: "ok" | "error";
  error_code: string | null;
  intent: string | null;
  query: Query | null;
  clarification: string | null;
  answer: { value_paise: number | null; count: number; items: Record<string, unknown>[] } | null;
};
export type Dashboard = {
  from: string;
  to: string;
  by_category: { category: string; value_paise: number; count: number }[];
  total_debit_paise: number;
  total_credit_paise: number;
  recent: Txn[];
};
export type Member = { id: number; name: string; position: number };
export type SplitPreview = { status: "preview"; code: string; payload: { description: string; amount: number } };

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
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new ApiError(data?.error?.message ?? `Request failed (${res.status})`, data?.error?.code ?? "HTTP_ERROR");
  }
  return data as T;
}

export const api = {
  parse: (messages: string[]) => request<{ results: ParseResult[] }>("/api/parse", "POST", { messages }),
  dashboard: (from?: string, to?: string) => {
    const qs = new URLSearchParams();
    if (from) qs.set("from", from);
    if (to) qs.set("to", to);
    const s = qs.toString();
    return request<Dashboard>(`/api/dashboard${s ? `?${s}` : ""}`);
  },
  ask: (question: string) => request<QueryResult>("/api/ask", "POST", { question }),
  groups: () => request<{ id: number; name: string; member_count: number }[]>("/api/splitease/groups"),
  group: (id: number) => request<{ id: number; name: string; members: Member[] }>(`/api/splitease/groups/${id}`),
  split: (tid: number, body: { group_id: number; paid_by: number; participants: number[]; confirm: boolean }) =>
    request<SplitPreview | { status: "created"; splitease_expense_id: number }>(`/api/transactions/${tid}/split`, "POST", body),
};
