from __future__ import annotations

import json
import sys
import types
import unittest
from safe_collection_operations.ankiconnect import ACTION_NAMES, install_ankiconnect_actions
from safe_collection_operations.mcp import MCPServer
from safe_collection_operations.registry import OperationRegistry, OperationSpec
from safe_collection_operations.service import DesktopService


class AdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        registry = OperationRegistry()
        registry.register(
            OperationSpec(
                name="echo",
                description="Echo a string.",
                input_schema={"type": "object"},
                handler=lambda _col, args: {"echo": args.get("value")},
            )
        )
        self.service = DesktopService(lambda: object(), registry=registry)

    def test_ankiconnect_extension_registers_namespaced_decorated_methods(self) -> None:
        module = types.ModuleType("AnkiConnectDev")

        class FakeAnkiConnect:
            pass

        module.AnkiConnect = FakeAnkiConnect
        previous = sys.modules.get("AnkiConnectDev")
        sys.modules["AnkiConnectDev"] = module
        try:
            full_registry = DesktopService(lambda: object())
            self.assertTrue(install_ankiconnect_actions(full_registry))
            for name in ACTION_NAMES:
                method = getattr(FakeAnkiConnect, name)
                self.assertTrue(method.api)
                self.assertTrue(method.safe_collection_operations)
            result = FakeAnkiConnect().safeCollectionOperationsCapabilities()
            self.assertEqual(result["api_version"], 1)
        finally:
            if previous is None:
                sys.modules.pop("AnkiConnectDev", None)
            else:
                sys.modules["AnkiConnectDev"] = previous

    def test_mcp_lists_and_calls_the_same_registry(self) -> None:
        server = MCPServer(self.service)
        initialized = server._handle(  # noqa: SLF001 - protocol unit test
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"},
            }
        )
        assert initialized is not None
        self.assertEqual(initialized["result"]["protocolVersion"], "2025-06-18")

        tools = server._handle(  # noqa: SLF001 - protocol unit test
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        )
        assert tools is not None
        self.assertEqual([tool["name"] for tool in tools["result"]["tools"]], ["echo"])

        called = server._handle(  # noqa: SLF001 - protocol unit test
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "echo", "arguments": {"value": "safe"}},
            }
        )
        assert called is not None
        content = called["result"]["content"][0]["text"]
        self.assertEqual(json.loads(content), {"echo": "safe"})


if __name__ == "__main__":
    unittest.main()
