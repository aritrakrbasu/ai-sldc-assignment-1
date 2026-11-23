"""MoneyLens FastAPI app (T016, T025, T029, T034, T036). Contract: contracts/api.md (M1-M8)."""

from __future__ import annotations

import datetime as dt
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from moneylens.ai import parser, qa
from moneylens.ai.llm import GeminiClient, LLMClient, ServiceError
from moneylens.config import PART_ROOT, load_settings
from moneylens.core.dashboard import summarize
from moneylens.core.dates import month_to_date
from moneylens.splitease_client import SplitEaseClient, SplitEaseError, SplitEaseUnavailable
from moneylens.storage.repository import Repository

from .schemas import AskIn, ParseIn, SplitIn

DEFAULT_DB = PART_ROOT / "data" / "moneylens.sqlite3"
STATIC = PART_ROOT / "frontend" / "dist"
MAX_BATCH = 50


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def _default_llm() -> LLMClient | None:
    try:
        return GeminiClient.from_settings(load_settings())
    except ServiceError:
        return None


def create_app(db_path: str | None = None, llm: LLMClient | None = None,
               splitease: SplitEaseClient | None = None, use_default_llm: bool = True) -> FastAPI:
    settings = load_settings()
    path = db_path or str(DEFAULT_DB)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    model = llm if llm is not None else (_default_llm() if use_default_llm else None)
    se = splitease or SplitEaseClient(settings.splitease_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.repo = Repository(path)
        yield
        app.state.repo.close()

    app = FastAPI(title="MoneyLens", version="1.0.0", lifespan=lifespan)

    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return _err(exc.status, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        resp = _err(422, "VALIDATION_ERROR", "Invalid request")
        return resp

    def repo(request: Request) -> Repository:
        return request.app.state.repo

    def today() -> str:
        return dt.date.today().isoformat()

    # ---- M1 ---------------------------------------------------------------------------
    @app.post("/api/parse")
    def parse_messages(body: ParseIn, request: Request):
        if not 1 <= len(body.messages) <= MAX_BATCH:
            raise ApiError(400, "INVALID_BATCH", "Send between 1 and 50 messages")
        ref = (body.reference_date or dt.date.today()).isoformat()
        results = parser.parse_batch(body.messages, ref, model)
        if body.save:
            for r in results:
                if r["status"] == "ok" and r["kind"] != "OTHER" \
                        and not repo(request).save_result(r, ref):
                    r.update(status="error", error_code="DUPLICATE")
        return {"results": results}

    # ---- M2, M3 -----------------------------------------------------------------------
    @app.get("/api/dashboard")
    def dashboard(request: Request, date_from: str | None = Query(None, alias="from"),
                  date_to: str | None = Query(None, alias="to")):
        start, end = month_to_date(dt.date.today())
        try:
            frm = dt.date.fromisoformat(date_from).isoformat() if date_from else start.isoformat()
            to = dt.date.fromisoformat(date_to).isoformat() if date_to else end.isoformat()
        except ValueError as exc:
            raise ApiError(422, "VALIDATION_ERROR", "Dates must be YYYY-MM-DD") from exc
        return summarize(repo(request).transactions_for_query(), frm, to)

    @app.get("/api/transactions")
    def transactions(request: Request, limit: int = 100):
        return repo(request).list_transactions(limit=max(1, min(limit, 500)))

    # ---- M4 ---------------------------------------------------------------------------
    @app.post("/api/ask")
    def ask(body: AskIn, request: Request):
        ref = (body.reference_date.isoformat() if body.reference_date else today())
        return qa.answer_question(body.question, ref, model,
                                  repo(request).transactions_for_query())

    # ---- M5, M6, M7 -------------------------------------------------------------------
    def splitease_call(fn, *args):
        try:
            return fn(*args)
        except SplitEaseUnavailable as exc:
            raise ApiError(502, "SPLITEASE_UNAVAILABLE",
                           "SplitEase is not reachable. Is it running?") from exc
        except SplitEaseError as exc:
            raise ApiError(exc.status, exc.code, exc.message) from exc

    @app.get("/api/splitease/groups")
    def splitease_groups():
        return splitease_call(se.list_groups)

    @app.get("/api/splitease/groups/{gid}")
    def splitease_group(gid: int):
        return splitease_call(se.get_group, gid)

    @app.post("/api/transactions/{tid}/split")
    def split(tid: int, body: SplitIn, request: Request):
        txn = repo(request).get_transaction(tid)
        if txn is None:
            raise ApiError(404, "TRANSACTION_NOT_FOUND", f"Transaction {tid} not found")
        if txn["direction"] != "DEBIT":
            raise ApiError(400, "NOT_A_DEBIT", "Only debits can be split")
        if txn["shared_expense_id"] is not None:
            raise ApiError(400, "ALREADY_SHARED", "This transaction was already sent")
        payload = {"description": (txn["merchant"] or "Bank transaction")[:120],
                   "amount": txn["amount_paise"], "paid_by": body.paid_by,
                   "date": txn["txn_date"] or txn["reference_date"], "split_mode": "EQUAL",
                   "splits": [{"member_id": m} for m in body.participants]}
        if not body.confirm:  # GR-4 / PROP-6: nothing is sent without confirmation
            return {"status": "preview", "code": "CONFIRMATION_REQUIRED", "payload": payload}
        created = splitease_call(se.create_expense, body.group_id, payload)
        repo(request).mark_shared(tid, int(created["id"]))
        return JSONResponse(status_code=201, content={"status": "created",
                                                      "splitease_expense_id": created["id"]})

    # ---- M8 ---------------------------------------------------------------------------
    @app.get("/api/health")
    def health():
        return {"model": getattr(model, "model", None), "model_configured": model is not None,
                "prompt_versions": {"parse": parser.PROMPT_VERSION, "query": qa.PROMPT_VERSION}}

    if STATIC.is_dir():
        app.mount("/", StaticFiles(directory=STATIC, html=True), name="spa")
    return app
