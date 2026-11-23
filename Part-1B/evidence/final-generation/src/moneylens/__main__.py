"""`python -m moneylens` — API + web UI on http://127.0.0.1:8100."""

import uvicorn

from moneylens.api.app import create_app


def main() -> None:
    uvicorn.run(create_app(), host="127.0.0.1", port=8100)


if __name__ == "__main__":
    main()
