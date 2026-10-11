"""Runtime settings for the demo: where the claims database lives."""

import os
from pathlib import Path

# demo/core/settings.py -> project root is three levels up
DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "claims_hub.sqlite"
DB_ENV_VAR = "CLAIMS_HUB_DB"


class DatabaseMissingError(FileNotFoundError):
    """Raised when the claims database file does not exist."""


def database_path() -> Path:
    """Return the database path from CLAIMS_HUB_DB, or the project default.

    Raises DatabaseMissingError with a message that says how to fix it.
    """
    path = Path(os.environ.get(DB_ENV_VAR) or DEFAULT_DB_PATH)
    if not path.is_file():
        raise DatabaseMissingError(
            f"Claims database not found at {path}. "
            f"Place claims_hub.sqlite in the project root or set {DB_ENV_VAR}."
        )
    return path
