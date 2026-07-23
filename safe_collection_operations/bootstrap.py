"""Anki desktop lifecycle wiring."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .ankiconnect import install_ankiconnect_actions
from .mcp import MCPServer
from .service import DesktopService


_service: DesktopService | None = None
_mcp_server: MCPServer | None = None
_ankiconnect_installed = False


def get_desktop_service() -> DesktopService:
    if _service is None:
        raise RuntimeError("Safe Collection Operations has not initialized")
    return _service


def initialize(addon_module_name: str, addon_root: Path) -> None:
    """Initialize once when Anki loads the add-on root module."""

    global _service
    if _service is not None:
        return

    from aqt import gui_hooks, mw

    _service = DesktopService(
        lambda: mw.col,
        run_on_main=lambda callback: mw.taskman.run_on_main(callback),
    )

    def config() -> dict[str, Any]:
        return mw.addonManager.getConfig(addon_module_name) or {}

    def on_profile_open() -> None:
        global _ankiconnect_installed, _mcp_server
        settings = config()
        if bool(settings.get("ankiconnect_enabled", True)):
            _ankiconnect_installed = install_ankiconnect_actions(get_desktop_service())
        if bool(settings.get("mcp_enabled", False)) and _mcp_server is None:
            host = str(settings.get("mcp_host", "127.0.0.1"))
            if host not in {"127.0.0.1", "localhost", "::1"}:
                raise RuntimeError("MCP may only bind to a loopback address")
            _mcp_server = MCPServer(
                get_desktop_service(),
                host=host,
                port=int(settings.get("mcp_port", 0)),
                discovery_file=addon_root / "user_files" / "mcp.json",
            )
            _mcp_server.start()

    def on_profile_close() -> None:
        global _mcp_server
        if _mcp_server is not None:
            _mcp_server.stop()
            _mcp_server = None

    gui_hooks.profile_did_open.append(on_profile_open)
    gui_hooks.profile_will_close.append(on_profile_close)
    if mw.col is not None:
        on_profile_open()


def transport_status() -> dict[str, Any]:
    return {
        "ankiconnect_actions_registered": _ankiconnect_installed,
        "mcp_url": _mcp_server.url if _mcp_server is not None else None,
    }
