"""Optional namespaced actions registered into an installed AnkiConnect."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Any, Mapping

from .service import DesktopService


ACTION_NAMES = (
    "safeCollectionOperationsCapabilities",
    "safeCollectionOperationsInspectCards",
    "safeCollectionOperationsGetGradingCursor",
    "safeCollectionOperationsFailCardsNow",
    "safeCollectionOperationsMakeCardsAvailable",
)
_ANKICONNECT_MODULE_CANDIDATES = ("2055492159", "AnkiConnectDev")


def _find_ankiconnect() -> ModuleType | None:
    for name in _ANKICONNECT_MODULE_CANDIDATES:
        module = sys.modules.get(name)
        if module is None:
            try:
                module = importlib.import_module(name)
            except ModuleNotFoundError:
                continue
        if hasattr(module, "AnkiConnect"):
            return module
    return None


def _mark_api(function: Any) -> Any:
    function.api = True
    function.versions = []
    function.safe_collection_operations = True
    return function


def install_ankiconnect_actions(service: DesktopService) -> bool:
    """Add namespaced actions to AnkiConnect's dynamically inspected class.

    AnkiConnect discovers decorated bound methods on every request, so adding
    methods to its class works for an already-running server. If a future
    AnkiConnect changes that contract, installation fails closed and the other
    transports remain available.
    """

    module = _find_ankiconnect()
    if module is None:
        return False
    target_class = module.AnkiConnect

    @_mark_api
    def safeCollectionOperationsCapabilities(_self: Any) -> dict[str, Any]:
        return service.execute("capabilities", {})

    @_mark_api
    def safeCollectionOperationsFailCardsNow(
        _self: Any,
        targets: list[Mapping[str, Any]],
        event: Mapping[str, Any],
    ) -> dict[str, Any]:
        return service.execute("fail_cards_now", {"targets": targets, "event": event})

    @_mark_api
    def safeCollectionOperationsInspectCards(
        _self: Any,
        card_ids: list[int],
    ) -> dict[str, Any]:
        return service.execute("inspect_cards", {"card_ids": card_ids})

    @_mark_api
    def safeCollectionOperationsGetGradingCursor(
        _self: Any,
        stream_id: str,
    ) -> dict[str, Any]:
        return service.execute("get_grading_cursor", {"stream_id": stream_id})

    @_mark_api
    def safeCollectionOperationsMakeCardsAvailable(
        _self: Any,
        card_ids: list[int],
    ) -> dict[str, Any]:
        return service.execute("make_cards_available", {"card_ids": card_ids})

    methods = {
        ACTION_NAMES[0]: safeCollectionOperationsCapabilities,
        ACTION_NAMES[1]: safeCollectionOperationsInspectCards,
        ACTION_NAMES[2]: safeCollectionOperationsGetGradingCursor,
        ACTION_NAMES[3]: safeCollectionOperationsFailCardsNow,
        ACTION_NAMES[4]: safeCollectionOperationsMakeCardsAvailable,
    }
    for name, method in methods.items():
        existing = getattr(target_class, name, None)
        if existing is not None and not getattr(existing, "safe_collection_operations", False):
            raise RuntimeError(f"AnkiConnect action name is already owned: {name}")
        setattr(target_class, name, method)
    return True
