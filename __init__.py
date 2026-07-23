"""Anki add-on bootstrap."""

from pathlib import Path

from .safe_collection_operations import *  # noqa: F403
from .safe_collection_operations.bootstrap import initialize


initialize(__name__, Path(__file__).resolve().parent)

