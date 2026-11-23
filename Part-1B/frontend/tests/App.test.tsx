// T037 [US6] — UI behaviour with a mocked API.
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "../src/App";

type Handler = (url: string, init?: RequestInit) => { status: number; body?: unknown };

function mockFetch(handler: Handler) {
  const fn = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    const { status, body } = handler(url, init);
    return new Response(body === undefined ? null : JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

const META = { model: "m", model_version: null, temperature: 0.2, prompt_version: "parse_sms.v1" };
const TXN_RESULT = {
  index: 0,
  status: "ok",
  error_code: null,
  masked_text: "Rs.250.00 debited from A/c XX4821 to VPA swiggy@icici",
  kind: "TRANSACTION",
  transaction: {
    amount_paise: 25000,
    direction: "DEBIT",
    merchant: "Swiggy",
    account_last4: "4821",
    txn_date: "2026-11-18",
    channel: "UPI",
    category: "FOOD",
  },
  bill: null,
  phishing: null,
  meta: META,
};
const PHISH_RESULT = {
  ...TXN_RESULT,
  index: 1,
  masked_text: "Your KYC expires, update at http://bit.ly/x9",
  kind: "PHISHING_SUSPECT",
  transaction: null,
  phishing: { reasons: ["SUSPICIOUS_LINK", "KYC_UPDATE_LURE"] },
};
const STORED = [
  { id: 7, amount_paise: 25000, direction: "DEBIT", merchant: "Swiggy", account_last4: "4821", txn_date: "2026-11-18",
    channel: "UPI", category: "FOOD", shared_expense_id: null, masked_text: TXN_RESULT.masked_text, reference_date: "2026-11-23" },
];

afterEach(() => vi.unstubAllGlobals());

function defaults(url: string) {
  if (url.startsWith("/api/health")) return { status: 200, body: { model: "m", model_configured: true, prompt_versions: {} } };
  if (url.startsWith("/api/transactions")) return { status: 200, body: STORED };
  if (url.startsWith("/api/dashboard"))
    return { status: 200, body: { from: "2026-11-01", to: "2026-11-23", by_category: [{ category: "FOOD", value_paise: 25000, count: 1 }],
      total_debit_paise: 25000, total_credit_paise: 0, recent: STORED } };
  return { status: 404, body: { error: { code: "NOT_FOUND", message: "x" } } };
}

describe("Inbox (US1, US6)", () => {
  it("parses pasted messages split by blank lines and shows cards", async () => {
    const fetchMock = mockFetch((url, init) =>
      url === "/api/parse" && init?.method === "POST"
        ? { status: 200, body: { results: [TXN_RESULT, PHISH_RESULT] } }
        : defaults(url),
    );
    render(<App />);
    const user = userEvent.setup();
    await user.type(screen.getByLabelText("Paste SMS messages"), "sms one{enter}{enter}sms two");
    await user.click(screen.getByRole("button", { name: "Parse messages" }));
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/parse",
        expect.objectContaining({ method: "POST", body: JSON.stringify({ messages: ["sms one", "sms two"] }) }),
      ),
    );
    const cards = await screen.findAllByRole("article");
    expect(cards).toHaveLength(2);
    expect(within(cards[0]).getByText("₹250.00")).toBeInTheDocument();
    expect(within(cards[0]).getByText("Swiggy")).toBeInTheDocument();
  });

  it("phishing card lists reasons and has no split action (US6-2)", async () => {
    mockFetch((url, init) =>
      url === "/api/parse" && init?.method === "POST"
        ? { status: 200, body: { results: [PHISH_RESULT] } }
        : defaults(url),
    );
    render(<App />);
    const user = userEvent.setup();
    await user.type(screen.getByLabelText("Paste SMS messages"), "scam");
    await user.click(screen.getByRole("button", { name: "Parse messages" }));
    const card = await screen.findByRole("article");
    expect(within(card).getByText(/Suspected phishing/)).toBeInTheDocument();
    expect(within(card).getByText("Suspicious link")).toBeInTheDocument();
    expect(within(card).queryByRole("button", { name: /Split/ })).toBeNull();
  });
});

describe("Ask (US4)", () => {
  it("shows interpreted filters and the computed answer", async () => {
    mockFetch((url, init) =>
      url === "/api/ask" && init?.method === "POST"
        ? {
            status: 200,
            body: {
              status: "ok", error_code: null, question: "food last week?", reference_date: "2026-11-23",
              intent: "SPEND_QUERY",
              query: { metric: "TOTAL", direction: "DEBIT", categories: ["FOOD"], merchant_contains: null,
                date_from: "2026-11-16", date_to: "2026-11-22", period_defaulted: false },
              clarification: null, answer: { value_paise: 65000, count: 2, items: [] }, meta: META,
            },
          }
        : defaults(url),
    );
    render(<App />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("tab", { name: "Ask" }));
    await user.type(screen.getByLabelText("Your question"), "food last week?");
    await user.click(screen.getByRole("button", { name: "Ask" }));
    expect(await screen.findByText("₹650.00")).toBeInTheDocument();
    expect(screen.getByText(/2026-11-16 → 2026-11-22/)).toBeInTheDocument();
    expect(screen.getByText(/FOOD/)).toBeInTheDocument();
  });

  it("shows the clarification and no number for out-of-scope", async () => {
    mockFetch((url, init) =>
      url === "/api/ask" && init?.method === "POST"
        ? { status: 200, body: { status: "ok", error_code: null, question: "gold?", reference_date: "2026-11-23",
            intent: "OUT_OF_SCOPE", query: null, clarification: "I can only answer questions about your transactions.",
            answer: null, meta: META } }
        : defaults(url),
    );
    render(<App />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("tab", { name: "Ask" }));
    await user.type(screen.getByLabelText("Your question"), "gold?");
    await user.click(screen.getByRole("button", { name: "Ask" }));
    expect(await screen.findByText(/only answer questions about your transactions/)).toBeInTheDocument();
    expect(screen.queryByText(/₹/)).toBeNull();
  });
});

describe("Split dialog (US5)", () => {
  it("requires preview then explicit confirmation", async () => {
    const posts: unknown[] = [];
    mockFetch((url, init) => {
      if (url === "/api/splitease/groups") return { status: 200, body: [{ id: 1, name: "Flat", member_count: 2 }] };
      if (url === "/api/splitease/groups/1")
        return { status: 200, body: { id: 1, name: "Flat", members: [{ id: 11, name: "Riya", position: 0 }, { id: 12, name: "Sam", position: 1 }] } };
      if (url === "/api/transactions/7/split" && init?.method === "POST") {
        const body = JSON.parse(String(init.body));
        posts.push(body);
        return body.confirm
          ? { status: 201, body: { status: "created", splitease_expense_id: 99 } }
          : { status: 200, body: { status: "preview", code: "CONFIRMATION_REQUIRED", payload: { description: "Swiggy", amount: 25000 } } };
      }
      return defaults(url);
    });
    render(<App />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("tab", { name: "Dashboard" }));
    await user.click(await screen.findByRole("button", { name: "Split Swiggy in SplitEase" }));
    const dialog = await screen.findByRole("dialog");
    await within(dialog).findByRole("checkbox", { name: "Riya" });
    await user.click(within(dialog).getByRole("button", { name: "Preview" }));
    expect(await within(dialog).findByText(/Swiggy · ₹250.00 · split equally between 2/)).toBeInTheDocument();
    expect(posts).toHaveLength(1);
    await user.click(within(dialog).getByRole("button", { name: "Confirm and send" }));
    expect(await screen.findByText(/Sent to SplitEase/)).toBeInTheDocument();
    expect(posts).toEqual([
      { group_id: 1, paid_by: 11, participants: [11, 12], confirm: false },
      { group_id: 1, paid_by: 11, participants: [11, 12], confirm: true },
    ]);
  });
});
