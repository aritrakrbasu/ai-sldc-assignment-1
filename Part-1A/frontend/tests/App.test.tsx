// T043 [US7] — UI behaviour with a mocked API (US7-1, US7-2, US7-3).
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
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

const GROUP = {
  id: 1,
  name: "Flat 4B",
  members: [
    { id: 11, name: "Asha", position: 0 },
    { id: 12, name: "Bilal", position: 1 },
    { id: 13, name: "Chen", position: 2 },
  ],
};
const EMPTY_DETAIL = {
  ...GROUP,
  expenses: [],
  settlements: [],
  balances: GROUP.members.map((m) => ({ member_id: m.id, name: m.name, balance: 0 })),
  settle_up: [],
};

beforeEach(() => {
  window.location.hash = "";
});
afterEach(() => {
  vi.unstubAllGlobals();
});

describe("US7-1 home page", () => {
  it("lists groups from the API", async () => {
    mockFetch(() => ({ status: 200, body: [{ id: 1, name: "Flat 4B", member_count: 3 }] }));
    render(<App />);
    expect(screen.getByRole("heading", { name: "SplitEase" })).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: /Flat 4B/ })).toBeInTheDocument();
  });

  it("creates a group with members one per line", async () => {
    const fetchMock = mockFetch((url, init) => {
      if (url === "/api/groups" && init?.method === "POST") return { status: 201, body: GROUP };
      if (url === "/api/groups/1") return { status: 200, body: EMPTY_DETAIL };
      return { status: 200, body: [] };
    });
    render(<App />);
    const user = userEvent.setup();
    await user.type(screen.getByLabelText("Group name"), "Flat 4B");
    await user.type(screen.getByLabelText("Members (one per line)"), "Asha{enter}Bilal{enter}Chen");
    await user.click(screen.getByRole("button", { name: "Create group" }));
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/groups",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ name: "Flat 4B", members: ["Asha", "Bilal", "Chen"] }),
        }),
      ),
    );
    expect(await screen.findByRole("heading", { name: "Flat 4B" })).toBeInTheDocument();
  });
});

describe("US7-2 expense form validation", () => {
  it("blocks an amount with 3 decimals before calling the API (FR-022)", async () => {
    const fetchMock = mockFetch((url) =>
      url === "/api/groups/1" ? { status: 200, body: EMPTY_DETAIL } : { status: 200, body: [] },
    );
    window.location.hash = "#/groups/1";
    render(<App />);
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText("Description"), "Dinner");
    await user.type(screen.getByLabelText("Amount (₹)"), "12.345");
    await user.click(screen.getByRole("button", { name: "Add expense" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Use at most 2 decimal places");
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
  });

  it("shows the API error message verbatim and keeps state", async () => {
    mockFetch((url, init) => {
      if (url === "/api/groups/1/expenses" && init?.method === "POST")
        return {
          status: 400,
          body: { error: { code: "SPLIT_SUM_MISMATCH", message: "Exact amounts must add up to 500.00" } },
        };
      if (url === "/api/groups/1") return { status: 200, body: EMPTY_DETAIL };
      return { status: 200, body: [] };
    });
    window.location.hash = "#/groups/1";
    render(<App />);
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText("Description"), "Dinner");
    await user.type(screen.getByLabelText("Amount (₹)"), "500");
    await user.click(screen.getByRole("button", { name: "Add expense" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Exact amounts must add up to 500.00");
  });
});

describe("US7-3 panels refresh after mutation", () => {
  it("reloads balances and settle-up after adding an expense", async () => {
    let detail = EMPTY_DETAIL;
    mockFetch((url, init) => {
      if (url === "/api/groups/1/expenses" && init?.method === "POST") {
        detail = {
          ...EMPTY_DETAIL,
          balances: [
            { member_id: 11, name: "Asha", balance: 66666 },
            { member_id: 12, name: "Bilal", balance: -33333 },
            { member_id: 13, name: "Chen", balance: -33333 },
          ],
          settle_up: [
            { from_member: 12, to_member: 11, amount: 33333 },
            { from_member: 13, to_member: 11, amount: 33333 },
          ],
        };
        return { status: 201, body: {} };
      }
      if (url === "/api/groups/1") return { status: 200, body: detail };
      return { status: 200, body: [] };
    });
    window.location.hash = "#/groups/1";
    render(<App />);
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText("Description"), "Groceries");
    await user.type(screen.getByLabelText("Amount (₹)"), "1000");
    await user.click(screen.getByRole("button", { name: "Add expense" }));
    const balances = await screen.findByRole("region", { name: "Balances" });
    expect(await within(balances).findByText("₹666.66")).toBeInTheDocument();
    const settle = screen.getByRole("region", { name: "Settle up" });
    expect(within(settle).getAllByText(/pays Asha/)).toHaveLength(2);
  });

  it("renders user text as text, not HTML (constitution V)", async () => {
    mockFetch((url) =>
      url === "/api/groups"
        ? { status: 200, body: [{ id: 2, name: "<img src=x onerror=alert(1)>", member_count: 2 }] }
        : { status: 200, body: [] },
    );
    const { container } = render(<App />);
    expect(await screen.findByText("<img src=x onerror=alert(1)>")).toBeInTheDocument();
    expect(container.querySelector("img")).toBeNull();
  });
});
