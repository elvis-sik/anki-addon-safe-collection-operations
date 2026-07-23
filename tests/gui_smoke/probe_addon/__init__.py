"""Disposable real-Anki probe for the utility add-on."""

from __future__ import annotations

import json
import os
import traceback
from pathlib import Path

from aqt import gui_hooks, mw
from aqt.qt import QTimer


RESULT_ENV = "ANKI_ADDON_WORKBENCH_RESULT"
SETTLE_MS = 500


def run_checks() -> dict[str, object]:
    from anki.decks import FilteredDeckConfig
    from anki_safe_collection_operations import (
        EventRef,
        Target,
        fail_cards_now,
        make_cards_available,
    )

    assert mw is not None and mw.col is not None
    col = mw.col
    model = col.models.by_name("Basic")
    assert model is not None

    def add_card(label: str) -> tuple[object, int]:
        note = col.new_note(model)
        note["Front"] = f"Safe operation probe: {label}"
        note["Back"] = "Disposable collection only"
        col.add_note(note, col.decks.id("Default"))
        return note, int(note.card_ids()[0])

    def move_to_filtered(card_id: int, *, name: str, reschedule: bool) -> int:
        deck = col.sched.get_or_create_filtered_deck(0)
        deck.name = name
        deck.config.reschedule = reschedule
        del deck.config.search_terms[:]
        deck.config.search_terms.extend(
            [
                FilteredDeckConfig.SearchTerm(
                    search=f"cid:{card_id}",
                    limit=1,
                    order=FilteredDeckConfig.SearchTerm.ADDED,
                )
            ]
        )
        return int(col.sched.add_or_update_filtered_deck(deck).id)

    note, card_id = add_card("normal")
    before = col.get_card(card_id)
    reps_before = int(before.reps)
    revlogs_before = int(col.db.scalar("select count() from revlog where cid = ?", card_id))

    graded = fail_cards_now(
        col,
        [Target(card_id=card_id, note_guid=note.guid)],
        event=EventRef(stream_id="workbench", sequence=1, event_id="grade-probe"),
    )
    after = col.get_card(card_id)
    revlogs_after = int(col.db.scalar("select count() from revlog where cid = ?", card_id))
    retried = fail_cards_now(
        col,
        [Target(card_id=card_id, note_guid=note.guid)],
        event=EventRef(stream_id="workbench", sequence=1, event_id="grade-probe"),
    )

    col.sched.suspend_cards([card_id])
    available = make_cards_available(col, [card_id])
    visible_queue = int(col.get_card(card_id).queue)

    preview_note, preview_id = add_card("preview filtered")
    preview_deck = move_to_filtered(
        preview_id,
        name="Safe Operations Probe::Preview",
        reschedule=False,
    )
    preview_before = col.get_card(preview_id)
    assert int(preview_before.did) == preview_deck and int(preview_before.odid) != 0
    preview_home = int(preview_before.odid)
    preview_reps = int(preview_before.reps)
    preview_result = fail_cards_now(
        col,
        [Target(preview_id, preview_note.guid)],
        event=EventRef("workbench-preview", 1, "preview-probe"),
    )
    preview_after = col.get_card(preview_id)

    filtered_note, filtered_id = add_card("rescheduling filtered")
    filtered_deck = move_to_filtered(
        filtered_id,
        name="Safe Operations Probe::Rescheduling",
        reschedule=True,
    )
    filtered_before = col.get_card(filtered_id)
    assert int(filtered_before.did) == filtered_deck and int(filtered_before.odid) != 0
    filtered_reps = int(filtered_before.reps)
    filtered_result = fail_cards_now(
        col,
        [Target(filtered_id, filtered_note.guid)],
        event=EventRef("workbench-rescheduling", 1, "rescheduling-probe"),
    )

    hidden_checks: list[dict[str, object]] = []
    for label, queue, manual in (
        ("suspension", -1, None),
        ("scheduler burial", -2, False),
        ("manual burial", -3, True),
    ):
        hidden_note, hidden_id = add_card(label)
        if manual is None:
            col.sched.suspend_cards([hidden_id])
        else:
            col.sched.bury_cards([hidden_id], manual=manual)
        hidden_reps = int(col.get_card(hidden_id).reps)
        hidden_result = fail_cards_now(
            col,
            [Target(hidden_id, hidden_note.guid)],
            event=EventRef(f"workbench-{label}", 1, f"{label}-probe"),
        )
        hidden_checks.append(
            {
                "name": f"preserves exact {label}",
                "ok": int(col.get_card(hidden_id).queue) == queue
                and int(col.get_card(hidden_id).reps) == hidden_reps + 1
                and hidden_id
                in (
                    hidden_result.preserved_suspended
                    + hidden_result.preserved_sched_buried
                    + hidden_result.preserved_user_buried
                ),
            }
        )

    checks = [
        {
            "name": "native Again changes reps once",
            "ok": int(after.reps) == reps_before + 1,
            "before": reps_before,
            "after": int(after.reps),
        },
        {
            "name": "native Again writes one revlog entry",
            "ok": revlogs_after == revlogs_before + 1,
            "before": revlogs_before,
            "after": revlogs_after,
        },
        {
            "name": "same event retry is a no-op",
            "ok": retried.already_applied and int(col.get_card(card_id).reps) == reps_before + 1,
        },
        {
            "name": "make available uses native restore",
            "ok": available.restored_suspended == (card_id,) and visible_queue >= 0,
            "queue": visible_queue,
        },
        {
            "name": "result identifies exact card",
            "ok": graded.card_ids == (card_id,),
        },
        {
            "name": "preview card exits alone and receives Again at home",
            "ok": preview_result.preview_exits == (preview_id,)
            and int(preview_after.did) == preview_home
            and int(preview_after.odid) == 0
            and int(preview_after.reps) == preview_reps + 1,
        },
        {
            "name": "rescheduling filtered card receives native Again",
            "ok": filtered_result.rescheduling_filtered == (filtered_id,)
            and int(col.get_card(filtered_id).reps) == filtered_reps + 1,
        },
        *hidden_checks,
    ]
    return {"ok": all(check["ok"] for check in checks), "checks": checks}


def finish() -> None:
    result_path = os.environ.get(RESULT_ENV)
    try:
        payload = run_checks()
    except Exception as exc:
        payload = {"ok": False, "error": str(exc), "traceback": traceback.format_exc()}
    if result_path:
        Path(result_path).write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    if mw is not None:
        mw.unloadProfileAndExit()


gui_hooks.main_window_did_init.append(lambda: QTimer.singleShot(SETTLE_MS, finish))
