# Configuration

- `ankiconnect_enabled`: register the add-on's namespaced actions when
  AnkiConnect is installed. Enabled by default.
- `mcp_enabled`: run the optional authenticated MCP adapter inside Anki.
  Disabled by default.
- `mcp_host`: MCP bind address. Keep this at `127.0.0.1` unless you have a
  separately secured local-network design.
- `mcp_port`: MCP port. `0` selects an available ephemeral port.

The MCP adapter writes its ephemeral URL and bearer token to the add-on's
ignored `user_files/mcp.json` discovery file. Treat that file as a local
credential.

