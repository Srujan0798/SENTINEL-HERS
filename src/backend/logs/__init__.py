"""Logs domain package.

Importing `models` here registers the log_entries/alerts tables on Base.metadata
so conftest's `from src.backend.logs import models` (and create_all) sees them.
"""
from . import models  # noqa: F401

__all__ = ["models"]
