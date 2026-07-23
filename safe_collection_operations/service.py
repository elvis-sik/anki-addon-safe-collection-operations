"""Desktop service facade and main-thread marshalling."""

from __future__ import annotations

import threading
from typing import Any, Callable, Mapping

from .models import OperationError
from .registry import OperationRegistry, build_registry


class DesktopService:
    def __init__(
        self,
        collection_provider: Callable[[], Any],
        *,
        run_on_main: Callable[[Callable[[], None]], None] | None = None,
        registry: OperationRegistry | None = None,
    ) -> None:
        self._collection_provider = collection_provider
        self._run_on_main = run_on_main
        self.registry = registry or build_registry()

    def execute(self, name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        collection = self._collection_provider()
        if collection is None:
            raise OperationError("Anki collection is not open")
        return self.registry.execute(collection, name, arguments)

    def execute_on_main(
        self,
        name: str,
        arguments: Mapping[str, Any],
        *,
        timeout_seconds: float = 30,
    ) -> dict[str, Any]:
        if self._run_on_main is None:
            return self.execute(name, arguments)

        done = threading.Event()
        box: dict[str, Any] = {}

        def run() -> None:
            try:
                box["result"] = self.execute(name, arguments)
            except BaseException as exc:
                box["error"] = exc
            finally:
                done.set()

        self._run_on_main(run)
        if not done.wait(timeout_seconds):
            raise OperationError("timed out waiting for Anki's main thread")
        if "error" in box:
            raise box["error"]
        return box["result"]

