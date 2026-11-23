"""SplitEase (Part 1A) HTTP client (T036, FR-015..FR-017, research R8)."""

from __future__ import annotations

import httpx


class SplitEaseUnavailable(Exception):
    pass


class SplitEaseError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


class SplitEaseClient:
    def __init__(self, base_url: str, transport: httpx.BaseTransport | None = None,
                 timeout: float = 5.0) -> None:
        self._client = httpx.Client(base_url=base_url, transport=transport, timeout=timeout)

    def _request(self, method: str, path: str, **kw) -> dict | list:
        try:
            resp = self._client.request(method, path, **kw)
        except httpx.HTTPError as exc:
            raise SplitEaseUnavailable(str(exc)) from exc
        if resp.status_code >= 400:
            try:
                err = resp.json().get("error", {})
            except ValueError:
                err = {}
            raise SplitEaseError(resp.status_code, err.get("code", "SPLITEASE_ERROR"),
                                 err.get("message", f"SplitEase returned {resp.status_code}"))
        return resp.json()

    def list_groups(self) -> list:
        return self._request("GET", "/api/groups")  # type: ignore[return-value]

    def get_group(self, gid: int) -> dict:
        return self._request("GET", f"/api/groups/{gid}")  # type: ignore[return-value]

    def create_expense(self, gid: int, payload: dict) -> dict:
        return self._request("POST", f"/api/groups/{gid}/expenses", json=payload)  # type: ignore[return-value]
