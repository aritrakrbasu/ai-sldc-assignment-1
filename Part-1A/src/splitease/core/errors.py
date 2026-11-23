"""Domain errors (T005). Codes are listed in data-model.md "Error codes (core)"."""

from __future__ import annotations


class DomainError(Exception):
    """A business-rule violation with a stable, machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
