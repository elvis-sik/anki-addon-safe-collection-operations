# Public API

## Compatibility

The initial release requires Anki 25.07 or newer because it delegates arbitrary
card answers to the native Browser **Grade Now** backend introduced in that
release. The implementation uses the collection backend directly, so it does
not depend on a Browser window.

## `inspect_cards`

Resolves exact card IDs to note GUIDs and scheduler context before grading.
Transport clients should use these stable target objects instead of trusting a
card-to-note mapping captured earlier.

## `get_grading_cursor`

Returns the last committed sequence and event ID for a caller-owned stream. A
new event uses the next sequence; an uncertain retry reuses the same sequence
and event ID.

## `fail_cards_now`

Inputs:

- `col`: the open Anki collection;
- `targets`: exact card IDs, with note GUIDs required for event-driven calls;
- `event`: an immutable `(stream_id, sequence, event_id)` position.

The event stream is contiguous. Repeating the current or an older position is
a no-op; gaps, stream-position reuse, malformed cursor state, stale note GUIDs,
and corrupt filtered-deck state fail closed.

Results include:

- affected card IDs;
- whether the event was already applied;
- preview-filter exits and rescheduling-filter cards;
- suspension, manual burial, and scheduler burial preserved after grading;
- cards newly suspended by native leech handling;
- warnings that did not invalidate the scheduler write.

## `make_cards_available`

Restores exact suspended or buried cards through Anki's native scheduler
operation. It does not remove or rewrite review history. Calling it again on
already-available cards is harmless.

## Transport names

Python uses snake case. AnkiConnect uses namespaced camel case. MCP uses
snake-case tool names:

| Python | AnkiConnect | MCP |
|---|---|---|
| `capabilities` | `safeCollectionOperationsCapabilities` | `capabilities` |
| `inspect_cards` | `safeCollectionOperationsInspectCards` | `inspect_cards` |
| `get_grading_cursor` | `safeCollectionOperationsGetGradingCursor` | `get_grading_cursor` |
| `fail_cards_now` | `safeCollectionOperationsFailCardsNow` | `fail_cards_now` |
| `make_cards_available` | `safeCollectionOperationsMakeCardsAvailable` | `make_cards_available` |
