"""
seed_resource_tags.py
─────────────────────
Automatically applies AAP taxonomy tags and test-linkage game keys
to every resource in the database whose name matches a card in card_data.py.

Run from the project root:
    python seed_resource_tags.py

Safe to run multiple times — all writes are idempotent (INSERT OR IGNORE /
replace-then-insert pattern). Existing tag data is replaced per resource.

Requires:
  • db.py  in the same directory (or importable)
  • card_data.py  in the same directory (or importable)
  • The app's SQLite database (JAG_AAP.db or whatever DB_PATH points to)
"""

import os
import sys
import sqlite3
import difflib
from datetime import datetime, timezone

# ── Locate the database ───────────────────────────────────────────────────────
# Adjust this path if your DB lives elsewhere.
DB_PATH = os.environ.get("JAG_DB", os.path.join(os.path.dirname(__file__), "JAG_AAP.db"))

# ── D10 label → game_key mapping ─────────────────────────────────────────────
# Maps the human-readable D10 tag value in card_data.py to the game_key used
# in CORE_AAP_GAMES / resource_game_links.
D10_TO_GAME_KEY = {
    "Balance Catching":      "balance_ball_catching",
    "Lob Scotch":            "lob_scotch",
    "Grid Leap":             "leap_catching_throwing",
    "Step Up":               "step_up",
    "Skipping Rope Sprint":  "skipping_rope_sprint",
    "Diamond Gates":         "diamond_gates",
    "Diamond Dribble":       "diamond_dribble",
    "Split Step":            "split_step",
    # Programme games that target multiple tests:
    "Ball Control":          None,   # no single test — skip game-link
    "Cross-Family":          None,   # general adaptability — skip game-link
}


def get_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def find_resource_id(conn, card_title: str) -> int | None:
    """Return resource.id whose name best matches card_title, or None."""
    rows = conn.execute("SELECT id, name FROM resources").fetchall()
    if not rows:
        return None

    names = [r["name"] for r in rows]
    # Try exact match first (case-insensitive)
    for r in rows:
        if r["name"].strip().lower() == card_title.strip().lower():
            return r["id"]

    # Fall back to close match
    matches = difflib.get_close_matches(card_title, names, n=1, cutoff=0.75)
    if matches:
        for r in rows:
            if r["name"] == matches[0]:
                return r["id"]

    return None


def set_taxonomy_tags(conn, resource_id: int, tags: dict) -> None:
    """Replace resource_taxonomy_tags for this resource (idempotent)."""
    conn.execute(
        "DELETE FROM resource_taxonomy_tags WHERE resource_id = ?", (resource_id,)
    )
    for dimension, values in tags.items():
        if dimension in ("D5", "D7"):      # scalar dimensions — store as-is
            for v in (values if isinstance(values, list) else [values]):
                if v:
                    conn.execute(
                        "INSERT OR IGNORE INTO resource_taxonomy_tags "
                        "(resource_id, dimension, value) VALUES (?, ?, ?)",
                        (resource_id, dimension, v),
                    )
        else:
            for v in (values if isinstance(values, list) else [values]):
                if v:
                    conn.execute(
                        "INSERT OR IGNORE INTO resource_taxonomy_tags "
                        "(resource_id, dimension, value) VALUES (?, ?, ?)",
                        (resource_id, dimension, v),
                    )
    conn.commit()


def set_game_links(conn, resource_id: int, d10_tags: list[str]) -> None:
    """Replace resource_game_links for this resource (idempotent)."""
    conn.execute(
        "DELETE FROM resource_game_links WHERE resource_id = ?", (resource_id,)
    )
    for label in d10_tags:
        game_key = D10_TO_GAME_KEY.get(label)
        if game_key:
            conn.execute(
                "INSERT OR IGNORE INTO resource_game_links (resource_id, game_key) VALUES (?, ?)",
                (resource_id, game_key),
            )
    conn.commit()


def ensure_resource_tags_exist(conn, all_cards: list) -> None:
    """Ensure the user-visible resource_tags rows exist for each D1 family."""
    families = set()
    for card in all_cards:
        for f in card.get("tags", {}).get("D1", []):
            families.add(f)

    now = datetime.now(timezone.utc).isoformat()
    for i, family in enumerate(sorted(families)):
        conn.execute(
            "INSERT OR IGNORE INTO resource_tags (name, sort_order, created_at) VALUES (?, ?, ?)",
            (family, i, now),
        )
    conn.commit()


def assign_d1_visible_tags(conn, resource_id: int, d1_tags: list[str]) -> None:
    """Assign the user-visible resource_tag rows for D1 families."""
    conn.execute(
        "DELETE FROM resource_tag_assignments WHERE resource_id = ?", (resource_id,)
    )
    for family in d1_tags:
        row = conn.execute(
            "SELECT id FROM resource_tags WHERE name = ?", (family,)
        ).fetchone()
        if row:
            conn.execute(
                "INSERT OR IGNORE INTO resource_tag_assignments (resource_id, tag_id) VALUES (?, ?)",
                (resource_id, row["id"]),
            )
    conn.commit()


def seed(db_path: str = DB_PATH) -> None:
    # card_data.py must be importable
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from card_data import ALL_CARDS  # noqa: PLC0415

    if not os.path.exists(db_path):
        print(f"ERROR: database not found at {db_path}")
        print("Set JAG_DB env var or adjust DB_PATH at top of this file.")
        sys.exit(1)

    conn = get_db(db_path)
    print(f"Connected to {db_path}")

    # Ensure D1 family tags exist in resource_tags table
    ensure_resource_tags_exist(conn, ALL_CARDS)

    tagged = 0
    skipped = 0

    for card in ALL_CARDS:
        title = card["title"]
        tags = card.get("tags", {})

        resource_id = find_resource_id(conn, title)
        if resource_id is None:
            print(f"  SKIP  (no resource match): {title}")
            skipped += 1
            continue

        # Structural taxonomy tags (D1–D9 stored in resource_taxonomy_tags)
        taxonomy = {
            dim: vals
            for dim, vals in tags.items()
            if dim != "D10" and vals
        }
        set_taxonomy_tags(conn, resource_id, taxonomy)

        # D10 test-linkage game keys (resource_game_links)
        set_game_links(conn, resource_id, tags.get("D10", []))

        # User-visible filter tags (resource_tag_assignments) = D1 families
        assign_d1_visible_tags(conn, resource_id, tags.get("D1", []))

        d1_str  = ", ".join(tags.get("D1",  ["-"]))
        d10_str = ", ".join(tags.get("D10", ["-"]))
        print(f"  OK    {title}")
        print(f"         D1={d1_str}  D10={d10_str}")
        tagged += 1

    print()
    print(f"Done — {tagged} resources tagged, {skipped} skipped (no DB match).")
    conn.close()


if __name__ == "__main__":
    seed()
