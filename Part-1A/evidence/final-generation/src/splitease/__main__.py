"""`python -m splitease` — run the API + built web UI on http://127.0.0.1:8000."""

import uvicorn

from splitease.api.app import create_app


def main() -> None:
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
