# Security

## Reporting

Please report security-sensitive findings privately through GitHub's security
advisory interface instead of opening a public issue.

## Boundaries

- The add-on never exposes arbitrary Python, SQL, filesystem, or `_backend`
  execution.
- MCP binds to loopback by default, requires a per-session bearer token, and is
  disabled unless explicitly enabled.
- AnkiConnect actions inherit AnkiConnect's own bind and API-key configuration.
- Operations accept exact identifiers and validate their current collection
  identity before writing.
- No user collection content, credentials, private service addresses, or local
  machine paths belong in this repository or its issue templates.

Anki add-ons execute with the desktop user's privileges. Install only code you
trust and review configuration before exposing any local API beyond loopback.

