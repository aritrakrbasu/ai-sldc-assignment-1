"""FastAPI application (T011, T022, T027, T032, T036, T038, T041). Contract: contracts/api.md.

The API validates input and persists data; every business rule is delegated to
``splitease.core`` (constitution Principle II).
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from splitease.core.balances import compute_balances
from splitease.core.errors import DomainError
from splitease.core.groups import validate_group_name, validate_members
from splitease.core.ledger_csv import build_csv
from splitease.core.model import Member, SplitInput
from splitease.core.settle import settle_up
from splitease.core.settlements import validate_settlement
from splitease.core.splitting import compute_shares
from splitease.storage.repository import Repository

from . import schemas as s

PART_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = PART_ROOT / "data" / "splitease.sqlite3"
STATIC_DIR = PART_ROOT / "frontend" / "dist"
NOT_FOUND_CODES = {"GROUP_NOT_FOUND", "EXPENSE_NOT_FOUND"}


def _error(status: int, code: str, message: str, **extra: object) -> JSONResponse:
    return JSONResponse(status_code=status,
                        content={"error": {"code": code, "message": message, **extra}})


def create_app(db_path: str | None = None) -> FastAPI:
    path = db_path or os.environ.get("SPLITEASE_DB") or str(DEFAULT_DB)
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.repo = Repository(path)
        yield
        app.state.repo.close()

    app = FastAPI(title="SplitEase", version="1.0.0", lifespan=lifespan)

    @app.exception_handler(DomainError)
    async def _domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return _error(404 if exc.code in NOT_FOUND_CODES else 400, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]
        return _error(422, "VALIDATION_ERROR", "Invalid request", details=details)

    def repo(request: Request) -> Repository:
        return request.app.state.repo

    def load_group(request: Request, gid: int) -> tuple[str, list[Member]]:
        found = repo(request).get_group(gid)
        if found is None:
            raise DomainError("GROUP_NOT_FOUND", f"Group {gid} does not exist")
        return found

    def ledger(request: Request, gid: int):
        name, members = load_group(request, gid)
        expenses = repo(request).list_expenses(gid)
        settlements = repo(request).list_settlements(gid)
        return name, members, expenses, settlements

    def expense_out(expense, inputs, members: list[Member]) -> s.ExpenseOut:
        order = {m.id: m.position for m in members}
        return s.ExpenseOut(
            id=expense.id, description=expense.description, amount=expense.amount,
            paid_by=expense.paid_by, date=expense.date, split_mode=expense.split_mode,
            splits=[s.SplitIn(member_id=i.member_id, amount=i.amount, percent=i.percent,
                              weight=i.weight)
                    for i in sorted(inputs, key=lambda i: order[i.member_id])],
            shares=[s.ShareOut(member_id=mid, amount=amt)
                    for mid, amt in sorted(expense.shares.items(), key=lambda kv: order[kv[0]])],
        )

    # ---- C1, C2, C3 -------------------------------------------------------------------
    @app.post("/api/groups", status_code=201, response_model=s.GroupOut)
    def create_group(body: s.GroupIn, request: Request):
        name = validate_group_name(body.name)
        names = validate_members(body.members)
        gid = repo(request).create_group(name, names)
        _, members = load_group(request, gid)
        return s.GroupOut(id=gid, name=name, members=[s.MemberOut(**vars(m)) for m in members])

    @app.get("/api/groups", response_model=list[s.GroupSummary])
    def list_groups(request: Request):
        return repo(request).list_groups()

    @app.get("/api/groups/{gid}", response_model=s.GroupDetail)
    def group_detail(gid: int, request: Request):
        name, members, expenses, settlements = ledger(request, gid)
        balances = compute_balances(members, [e for e, _ in expenses], settlements)
        names = {m.id: m.name for m in members}
        return s.GroupDetail(
            id=gid, name=name, members=[s.MemberOut(**vars(m)) for m in members],
            expenses=[expense_out(e, i, members) for e, i in expenses],
            settlements=[s.SettlementOut(id=x.id, from_member=x.from_member,
                                         to_member=x.to_member, amount=x.amount, date=x.date)
                         for x in settlements],
            balances=[s.BalanceOut(member_id=mid, name=names[mid], balance=b)
                      for mid, b in balances.items()],
            settle_up=[s.PaymentOut(**vars(p)) for p in settle_up(members, balances)],
        )

    # ---- C4, C5 -----------------------------------------------------------------------
    @app.post("/api/groups/{gid}/expenses", status_code=201, response_model=s.ExpenseOut)
    def add_expense(gid: int, body: s.ExpenseIn, request: Request):
        _, members = load_group(request, gid)
        inputs = [SplitInput(x.member_id, x.amount, x.percent, x.weight) for x in body.splits]
        shares = compute_shares(members, body.amount, body.paid_by, body.split_mode, inputs)
        eid = repo(request).add_expense(gid, body.description, body.amount, body.paid_by,
                                        body.date.isoformat(), body.split_mode, inputs, shares)
        for expense, stored_inputs in repo(request).list_expenses(gid):
            if expense.id == eid:
                return expense_out(expense, stored_inputs, members)
        raise RuntimeError("expense vanished after insert")  # pragma: no cover

    @app.delete("/api/groups/{gid}/expenses/{eid}", status_code=204)
    def delete_expense(gid: int, eid: int, request: Request):
        load_group(request, gid)
        if not repo(request).delete_expense(gid, eid):
            raise DomainError("EXPENSE_NOT_FOUND", f"Expense {eid} does not exist in this group")
        return Response(status_code=204)

    # ---- C6 (+ immutability) ----------------------------------------------------------
    @app.post("/api/groups/{gid}/settlements", status_code=201, response_model=s.SettlementOut)
    def add_settlement(gid: int, body: s.SettlementIn, request: Request):
        _, members = load_group(request, gid)
        validate_settlement(members, body.from_member, body.to_member, body.amount)
        date = body.date.isoformat()
        sid = repo(request).add_settlement(gid, body.from_member, body.to_member, body.amount,
                                           date)
        return s.SettlementOut(id=sid, from_member=body.from_member, to_member=body.to_member,
                               amount=body.amount, date=date)

    @app.api_route("/api/groups/{gid}/settlements/{sid}", methods=["DELETE", "PUT", "PATCH"])
    def settlement_immutable(gid: int, sid: int):
        return _error(405, "SETTLEMENT_IMMUTABLE",
                      "Settlements cannot be changed; record a reverse settlement instead")

    # ---- C7, C8, C9 -------------------------------------------------------------------
    @app.get("/api/groups/{gid}/balances", response_model=list[s.BalanceOut])
    def balances(gid: int, request: Request):
        _, members, expenses, settlements = ledger(request, gid)
        names = {m.id: m.name for m in members}
        bal = compute_balances(members, [e for e, _ in expenses], settlements)
        return [s.BalanceOut(member_id=mid, name=names[mid], balance=b) for mid, b in bal.items()]

    @app.get("/api/groups/{gid}/settle-up", response_model=list[s.PaymentOut])
    def settle(gid: int, request: Request):
        _, members, expenses, settlements = ledger(request, gid)
        bal = compute_balances(members, [e for e, _ in expenses], settlements)
        return [s.PaymentOut(**vars(p)) for p in settle_up(members, bal)]

    @app.get("/api/groups/{gid}/export.csv")
    def export_csv(gid: int, request: Request):
        name, members, expenses, settlements = ledger(request, gid)
        body = build_csv(members, [e for e, _ in expenses], settlements)
        return Response(
            content=body, media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="splitease-group-{gid}.csv"'},
        )

    if STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="spa")

    return app
