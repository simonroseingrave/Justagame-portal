"""SQLite data access layer. Pure standard library (sqlite3) -- no ORM."""
import os
import sqlite3
import datetime

from auth import hash_password

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "justagame.db")

# Run critical column migrations once per process on first connection
_MIGRATIONS_APPLIED = False

SCHEMA = """
CREATE TABLE IF NOT EXISTS organisations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT,
    icon_url TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('practitioner','org_admin','system_admin','participant')),
    is_admin INTEGER NOT NULL DEFAULT 0,
    sport TEXT,
    programme TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    organisation_id INTEGER REFERENCES organisations(id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    points_value INTEGER NOT NULL DEFAULT 25
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id INTEGER NOT NULL REFERENCES users(id),
    date TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT,
    notes TEXT,
    points INTEGER NOT NULL DEFAULT 0,
    logged_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS awards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id INTEGER NOT NULL REFERENCES users(id),
    achievement_id INTEGER NOT NULL REFERENCES achievements(id),
    date_awarded TEXT NOT NULL,
    awarded_by INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS measurement_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id INTEGER NOT NULL REFERENCES users(id),
    group_id INTEGER REFERENCES participant_groups(id),
    date TEXT NOT NULL,
    logged_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS measurement_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES measurement_sessions(id),
    game_key TEXT NOT NULL,
    field_key TEXT NOT NULL,
    value REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS participant_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    icon_url TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    organisation_id INTEGER REFERENCES organisations(id),
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resource_folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    added_by INTEGER REFERENCES users(id),
    folder_id INTEGER REFERENCES resource_folders(id),
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS coach_groups (
    coach_id INTEGER NOT NULL REFERENCES users(id),
    group_id INTEGER NOT NULL REFERENCES participant_groups(id),
    PRIMARY KEY (coach_id, group_id)
);

CREATE TABLE IF NOT EXISTS resource_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resource_tag_assignments (
    resource_id INTEGER NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES resource_tags(id) ON DELETE CASCADE,
    PRIMARY KEY (resource_id, tag_id)
);

-- ── Resource Taxonomy (hidden structural tags) ────────────────────────────
-- Links each resource to one or more AAP measurement games (D10 Test Linkage).
-- Separate from user-facing resource_tags; never shown to athletes.
CREATE TABLE IF NOT EXISTS resource_game_links (
    resource_id INTEGER NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
    game_key    TEXT NOT NULL,
    PRIMARY KEY (resource_id, game_key)
);

-- Multi-value taxonomy dimensions (D1, D2, D3, D4, D6, D8).
-- dimension is one of: D1, D2, D3, D4, D6, D8
-- value is the machine-readable slug for that dimension's option.
CREATE TABLE IF NOT EXISTS resource_taxonomy_tags (
    resource_id INTEGER NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
    dimension   TEXT NOT NULL,
    value       TEXT NOT NULL,
    PRIMARY KEY (resource_id, dimension, value)
);

-- ── Attendance & Self-Directed Sessions ──────────────────────────────────

-- A practitioner-created session event (one per training date per group).
-- Serves as the validity gate for athlete self-directed score entry.
CREATE TABLE IF NOT EXISTS session_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER REFERENCES participant_groups(id) ON DELETE SET NULL,
    date TEXT NOT NULL,
    notes TEXT,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL
);

-- Which athletes attended a session event. Marked by a practitioner.
-- One row per athlete per event. UNIQUE prevents double-marking.
CREATE TABLE IF NOT EXISTS session_attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL REFERENCES session_events(id) ON DELETE CASCADE,
    participant_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    marked_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    UNIQUE (event_id, participant_id)
);

-- ── XP Engine ─────────────────────────────────────────────────────────────

-- Append-only XP ledger. Every XP award is a separate row.
-- xp_type values: participation_formal, participation_self, pb_formal,
--   pb_self, ingame_formal, ingame_self, level_achievement, breadth_first_game,
--   streak_3, streak_5, welcome_bonus, all_8_session, all_8_l1
CREATE TABLE IF NOT EXISTS xp_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    xp_type TEXT NOT NULL,
    amount INTEGER NOT NULL,
    game_key TEXT,
    session_id INTEGER REFERENCES measurement_sessions(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TEXT NOT NULL
);

-- Append-only level achievement record. One row per (athlete × game × field_key × level).
-- field_key='' for games with a single scoring area; specific value for multi-field games (Balance Ball).
-- UNIQUE constraint prevents double-awarding. Never deleted.
CREATE TABLE IF NOT EXISTS level_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    game_key TEXT NOT NULL,
    field_key TEXT NOT NULL DEFAULT '',
    level INTEGER NOT NULL,
    session_id INTEGER REFERENCES measurement_sessions(id) ON DELETE SET NULL,
    awarded_at TEXT NOT NULL,
    UNIQUE (participant_id, game_key, field_key, level)
);

-- Admin-configurable threshold per (game × field_key × level).
-- field_key identifies the scoring area within a game (matches SCORING_AREAS).
-- Score at or above this value earns the level.
-- For skipping_rope_sprint (lower_is_better), score at or BELOW earns the level.
CREATE TABLE IF NOT EXISTS game_level_thresholds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_key TEXT NOT NULL,
    field_key TEXT NOT NULL DEFAULT '',
    level INTEGER NOT NULL,
    threshold_value REAL NOT NULL,
    lower_is_better INTEGER NOT NULL DEFAULT 0,
    set_by INTEGER REFERENCES users(id),
    updated_at TEXT NOT NULL,
    UNIQUE (game_key, field_key, level)
);

-- Per-athlete, per-game personal best tracking.
-- One row per (athlete × game × field). Updated in place when a new PB is set.
CREATE TABLE IF NOT EXISTS athlete_personal_bests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    game_key TEXT NOT NULL,
    field_key TEXT NOT NULL,
    best_value REAL NOT NULL,
    session_id INTEGER REFERENCES measurement_sessions(id) ON DELETE SET NULL,
    is_formal INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL,
    UNIQUE (participant_id, game_key, field_key)
);

-- Testing round: a group-level formal testing event at a specific level and type.
-- round_type: 'baseline' (first time at this level) or 'retest' (repeat for comparison).
-- retest_sequence: null for baseline; 1, 2, 3... for successive retests at same level.
-- Unlock rules enforced in Python: baseline requires previous level retest; retest requires baseline.
CREATE TABLE IF NOT EXISTS testing_rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES participant_groups(id),
    level INTEGER NOT NULL CHECK (level BETWEEN 1 AND 5),
    round_type TEXT NOT NULL CHECK (round_type IN ('baseline', 'retest')),
    retest_sequence INTEGER,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    opened_at TEXT NOT NULL,
    closed_at TEXT,
    opened_by INTEGER NOT NULL REFERENCES users(id),
    notes TEXT
);

-- Individual athlete scores recorded within a testing round.
-- One row per (round × athlete × game × field).
CREATE TABLE IF NOT EXISTS round_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id INTEGER NOT NULL REFERENCES testing_rounds(id),
    athlete_id INTEGER NOT NULL REFERENCES users(id),
    game_key TEXT NOT NULL,
    field_key TEXT NOT NULL,
    value REAL NOT NULL,
    recorded_at TEXT NOT NULL,
    recorded_by INTEGER NOT NULL REFERENCES users(id)
);

-- AXP awarded per athlete per game per round, calculated on round close.
-- award_type: 'baseline_participation', 'improvement', or 'completion_bonus'.
CREATE TABLE IF NOT EXISTS round_xp_awards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id INTEGER NOT NULL REFERENCES testing_rounds(id),
    athlete_id INTEGER NOT NULL REFERENCES users(id),
    game_key TEXT,
    improvement_pct REAL,
    xp_awarded INTEGER NOT NULL,
    award_type TEXT NOT NULL,
    awarded_at TEXT NOT NULL
);
"""


def get_conn():
    global _MIGRATIONS_APPLIED
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = lambda cur, row: dict(zip([d[0] for d in cur.description], row))
    conn.execute("PRAGMA foreign_keys = ON")
    if not _MIGRATIONS_APPLIED:
        _MIGRATIONS_APPLIED = True
        for sql in [
            "ALTER TABLE resources ADD COLUMN card_slug TEXT",
            "ALTER TABLE users ADD COLUMN onboarding_seen INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE session_events ADD COLUMN is_open INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE session_events ADD COLUMN opened_at TEXT",
            "ALTER TABLE participant_groups ADD COLUMN show_leaderboard INTEGER NOT NULL DEFAULT 0",
        ]:
            try:
                conn.execute(sql)
                conn.commit()
            except Exception:
                pass  # column already exists
    return conn


def migrate_diamond_group_fields(conn):
    """One-time migration: collapse the old per-athlete-count fields for Diamond
    Gates and Diamond Dribble into two simplified buckets — small_group (3-5
    athletes) and large_group (6-8 athletes).

    For each session that has old-style field keys, the highest value within
    each bucket is used (since only one count is usually recorded per session,
    this is typically a straight copy).  Old field_key rows are deleted after
    the new ones are written.  Safe to re-run: sessions already on the new
    schema have neither old keys to migrate nor existing new keys to clobber.
    """
    MAPPINGS = [
        # (game_key, [old field_keys], new field_key)
        ("diamond_gates",   ["athletes_3", "athletes_4", "athletes_5"], "small_group"),
        ("diamond_gates",   ["athletes_6", "athletes_7", "athletes_8"], "large_group"),
        ("diamond_dribble", ["athletes_4", "athletes_5"],               "small_group"),
        ("diamond_dribble", ["athletes_6"],                             "large_group"),
    ]

    for game_key, old_keys, new_key in MAPPINGS:
        placeholders = ",".join("?" * len(old_keys))
        rows = conn.execute(
            f"SELECT session_id, field_key, value FROM measurement_results "
            f"WHERE game_key = ? AND field_key IN ({placeholders}) "
            f"AND value IS NOT NULL AND value != ''",
            [game_key] + old_keys,
        ).fetchall()

        if not rows:
            continue  # nothing to migrate for this mapping

        # Find the best (max numeric) value per session within this bucket
        session_best = {}
        for row in rows:
            sid = row["session_id"]
            try:
                val = float(row["value"])
            except (TypeError, ValueError):
                continue
            if sid not in session_best or val > session_best[sid][0]:
                session_best[sid] = (val, row["value"])  # keep original string

        # Write to new field_key (only if not already present)
        for sid, (_, raw_val) in session_best.items():
            existing = conn.execute(
                "SELECT id FROM measurement_results "
                "WHERE session_id = ? AND game_key = ? AND field_key = ?",
                (sid, game_key, new_key),
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO measurement_results (session_id, game_key, field_key, value) "
                    "VALUES (?, ?, ?, ?)",
                    (sid, game_key, new_key, raw_val),
                )

        # Delete old field_key records now that new ones are written
        conn.execute(
            f"DELETE FROM measurement_results "
            f"WHERE game_key = ? AND field_key IN ({placeholders})",
            [game_key] + old_keys,
        )

    conn.commit()


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    # Self-heal if a previous run was interrupted mid-write and left a
    # corrupt/partial database file behind -- rebuild rather than crash.
    if os.path.exists(DB_PATH):
        try:
            probe = sqlite3.connect(DB_PATH)
            probe.execute("SELECT name FROM sqlite_master LIMIT 1")
            probe.close()
        except sqlite3.DatabaseError:
            for suffix in ("", "-journal", "-wal", "-shm"):
                stray = DB_PATH + suffix
                if os.path.exists(stray):
                    os.remove(stray)

    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    # Migrations: add columns to existing tables that pre-date this schema version.
    # ALTER TABLE ADD COLUMN silently fails if the column already exists.
    for sql in [
        "ALTER TABLE resources ADD COLUMN folder_id INTEGER REFERENCES resource_folders(id)",
        "ALTER TABLE resources ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN group_id INTEGER REFERENCES participant_groups(id)",
        "ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE participant_groups ADD COLUMN icon_url TEXT",
        "ALTER TABLE users ADD COLUMN username TEXT",
        "ALTER TABLE measurement_sessions ADD COLUMN group_id INTEGER REFERENCES participant_groups(id)",
        "ALTER TABLE users ADD COLUMN organisation TEXT",
        "ALTER TABLE users ADD COLUMN athlete_number TEXT",
        "ALTER TABLE users ADD COLUMN gender TEXT",
        "ALTER TABLE users ADD COLUMN organisation_id INTEGER REFERENCES organisations(id)",
        "ALTER TABLE participant_groups ADD COLUMN organisation_id INTEGER REFERENCES organisations(id)",
        "ALTER TABLE organisations ADD COLUMN icon_url TEXT",
        "ALTER TABLE resources ADD COLUMN self_organisation TEXT",
        "ALTER TABLE measurement_sessions ADD COLUMN session_label TEXT",
        "ALTER TABLE measurement_sessions ADD COLUMN session_month TEXT",
        "ALTER TABLE measurement_sessions ADD COLUMN session_type TEXT NOT NULL DEFAULT 'formal'",
        "ALTER TABLE measurement_sessions ADD COLUMN attendance_event_id INTEGER REFERENCES session_events(id)",
        "ALTER TABLE participant_groups ADD COLUMN show_leaderboard INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE resources ADD COLUMN level_range TEXT NOT NULL DEFAULT 'all'",
        "ALTER TABLE resources ADD COLUMN space_requirement TEXT NOT NULL DEFAULT 'unspecified'",
        "ALTER TABLE session_events ADD COLUMN is_open INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE session_events ADD COLUMN opened_at TEXT",
        "ALTER TABLE users ADD COLUMN onboarding_seen INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE resources ADD COLUMN card_slug TEXT",
    ]:
        try:
            conn.execute(sql)
            conn.commit()
        except Exception:
            pass  # column already exists
    # Data migration: align level_range values with taxonomy doc naming
    for old_val, new_val in [
        ("entry", "level_1"),
        ("developing", "level_2"),
        ("progressing", "level_3"),
        ("all", "multi_level"),
    ]:
        try:
            conn.execute("UPDATE resources SET level_range = ? WHERE level_range = ?", (new_val, old_val))
            conn.commit()
        except Exception:
            pass
    # Data migration: rename legacy game_keys to clean canonical names
    # diamond_games → diamond_gates  |  diamond_gym → step_up
    for table in ("measurement_results", "xp_events", "level_achievements",
                  "game_level_thresholds", "resource_game_links"):
        for old_key, new_key in (("diamond_games", "diamond_gates"), ("diamond_gym", "step_up")):
            try:
                conn.execute(f"UPDATE {table} SET game_key = ? WHERE game_key = ?", (new_key, old_key))
                conn.commit()
            except Exception:
                pass
    # Migration: rebuild level_achievements and game_level_thresholds to add
    # field_key discriminator column and updated UNIQUE constraints.
    # This is safe because both tables are empty until thresholds are set and
    # the retroactive XP pass runs. The migration is idempotent via column check.
    _migrate_level_tables(conn)
    # Retroactively assign athlete numbers to any participants added before
    # this feature was introduced.
    assign_missing_athlete_numbers(conn)
    # Migrate Diamond Gates / Diamond Dribble from per-athlete-count fields to
    # small_group / large_group (idempotent: skips sessions already migrated).
    migrate_diamond_group_fields(conn)
    # Migrate role values: 'coach' with is_admin=1 → 'system_admin',
    # 'coach' with is_admin=0 → 'practitioner' (idempotent).
    migrate_roles(conn)
    # Ensure every participant has their welcome bonus XP (idempotent).
    try:
        retroactive_welcome_bonus(conn)
    except Exception:
        pass
    conn.close()


def init_db_migrations(conn):
    """Run only the ALTER TABLE column migrations (safe to call at any time)."""
    for sql in [
        "ALTER TABLE resources ADD COLUMN card_slug TEXT",
        "ALTER TABLE users ADD COLUMN onboarding_seen INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE session_events ADD COLUMN is_open INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE session_events ADD COLUMN opened_at TEXT",
        "ALTER TABLE participant_groups ADD COLUMN show_leaderboard INTEGER NOT NULL DEFAULT 0",
    ]:
        try:
            conn.execute(sql)
            conn.commit()
        except Exception:
            pass  # column already exists


def _migrate_level_tables(conn):
    """Rebuild level_achievements and game_level_thresholds to add field_key column
    and update UNIQUE constraints to include it.

    SQLite cannot ALTER TABLE to change a UNIQUE constraint, so we use the
    standard CREATE NEW → COPY → DROP OLD → RENAME approach.

    Safe to run on a fresh DB (tables are already correct from SCHEMA) and
    idempotent on an already-migrated DB (column check skips the work).
    """
    # Check if level_achievements already has field_key
    cols_la = {row["name"] for row in conn.execute("PRAGMA table_info(level_achievements)").fetchall()}
    if "field_key" not in cols_la:
        conn.executescript("""
            BEGIN;
            CREATE TABLE IF NOT EXISTS level_achievements_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                game_key TEXT NOT NULL,
                field_key TEXT NOT NULL DEFAULT '',
                level INTEGER NOT NULL,
                session_id INTEGER REFERENCES measurement_sessions(id) ON DELETE SET NULL,
                awarded_at TEXT NOT NULL,
                UNIQUE (participant_id, game_key, field_key, level)
            );
            INSERT INTO level_achievements_new
                (id, participant_id, game_key, field_key, level, session_id, awarded_at)
            SELECT id, participant_id, game_key, '', level, session_id, awarded_at
            FROM level_achievements;
            DROP TABLE level_achievements;
            ALTER TABLE level_achievements_new RENAME TO level_achievements;
            COMMIT;
        """)

    # Check if game_level_thresholds already has the correct UNIQUE
    # (field_key column is already in the old schema, but UNIQUE was (game_key, level))
    # We detect by checking if a duplicate (game_key, field_key, level) insert would fail
    # in a way consistent with the new constraint — easiest is to check the index name.
    idx_rows = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='index' "
        "AND tbl_name='game_level_thresholds'"
    ).fetchall()
    has_new_unique = any(
        r["sql"] and "field_key" in r["sql"]
        for r in idx_rows
    )
    if not has_new_unique:
        conn.executescript("""
            BEGIN;
            CREATE TABLE IF NOT EXISTS game_level_thresholds_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_key TEXT NOT NULL,
                field_key TEXT NOT NULL DEFAULT '',
                level INTEGER NOT NULL,
                threshold_value REAL NOT NULL,
                lower_is_better INTEGER NOT NULL DEFAULT 0,
                set_by INTEGER REFERENCES users(id),
                updated_at TEXT NOT NULL,
                UNIQUE (game_key, field_key, level)
            );
            INSERT INTO game_level_thresholds_new
                (id, game_key, field_key, level, threshold_value, lower_is_better, set_by, updated_at)
            SELECT id, game_key, COALESCE(field_key, ''), level, threshold_value,
                   lower_is_better, set_by, updated_at
            FROM game_level_thresholds;
            DROP TABLE game_level_thresholds;
            ALTER TABLE game_level_thresholds_new RENAME TO game_level_thresholds;
            COMMIT;
        """)


def migrate_roles(conn):
    """Rename legacy 'coach' / 'admin' role values to 'practitioner' / 'system_admin'.
    Idempotent — safe to run on every startup.

    The old DB schema has CHECK(role IN ('coach','admin','participant')) which
    blocks an UPDATE to the new role names.  SQLite has no ALTER TABLE … DROP
    CONSTRAINT, so we patch sqlite_master directly and bump schema_version to
    flush the in-connection schema cache before running the UPDATEs.
    """
    import re as _re

    old_count = conn.execute(
        "SELECT COUNT(*) AS cnt FROM users WHERE role IN ('coach', 'admin')"
    ).fetchone()["cnt"]
    if old_count == 0:
        return  # Already migrated (or fresh install with new schema)

    # Patch the CHECK constraint in sqlite_master so the UPDATE is allowed
    schema_row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='users'"
    ).fetchone()
    if schema_row:
        old_sql = schema_row["sql"]
        new_sql = _re.sub(
            r"CHECK\s*\(\s*role\s+IN\s*\([^)]+\)\s*\)",
            "CHECK(role IN ('practitioner','org_admin','system_admin','participant'))",
            old_sql,
            flags=_re.IGNORECASE,
        )
        if new_sql != old_sql:
            schema_ver = conn.execute("PRAGMA schema_version").fetchone()["schema_version"]
            conn.execute("PRAGMA writable_schema = ON")
            conn.execute(
                "UPDATE sqlite_master SET sql = ? "
                "WHERE type = 'table' AND name = 'users'",
                (new_sql,),
            )
            # Bumping schema_version forces SQLite to reload the schema
            # from sqlite_master on the next statement, so our UPDATE below
            # will see the relaxed CHECK constraint.
            conn.execute(f"PRAGMA schema_version = {schema_ver + 1}")
            conn.execute("PRAGMA writable_schema = OFF")
            conn.commit()

    # Now migrate: is_admin=1 → system_admin, everyone else → practitioner
    conn.execute(
        "UPDATE users SET role = 'system_admin' "
        "WHERE role IN ('coach', 'admin') AND is_admin = 1"
    )
    conn.execute(
        "UPDATE users SET role = 'practitioner' WHERE role IN ('coach', 'admin')"
    )
    conn.commit()


def next_athlete_number(conn):
    """Return the next unused zero-padded 4-digit athlete number as a string."""
    row = conn.execute(
        "SELECT MAX(CAST(athlete_number AS INTEGER)) AS max_n "
        "FROM users WHERE athlete_number IS NOT NULL AND athlete_number GLOB '[0-9]*'"
    ).fetchone()
    max_n = row["max_n"] or 0
    return f"{max_n + 1:04d}"


def assign_missing_athlete_numbers(conn):
    """Retroactively assign athlete_number to participants who don't have one.
    Called once at startup so any pre-feature participants get a number."""
    participants = conn.execute(
        "SELECT id FROM users WHERE role='participant' AND athlete_number IS NULL ORDER BY id"
    ).fetchall()
    for p in participants:
        num = next_athlete_number(conn)
        conn.execute("UPDATE users SET athlete_number = ? WHERE id = ?", (num, p["id"]))
        conn.commit()


def find_or_create_group(conn, name, created_by, organisation_id=None):
    """Find a group by name (case-insensitive) or create it. Returns group_id.
    If organisation_id is given, also links the group to that organisation
    (both on creation and on an existing group that has no org yet)."""
    name = name.strip()
    row = conn.execute(
        "SELECT id, organisation_id FROM participant_groups WHERE lower(name) = lower(?)", (name,)
    ).fetchone()
    if row:
        gid = row["id"]
        # Link to org if not already linked
        if organisation_id and not row["organisation_id"]:
            conn.execute(
                "UPDATE participant_groups SET organisation_id = ? WHERE id = ?",
                (organisation_id, gid),
            )
            conn.commit()
        return gid
    max_order = conn.execute(
        "SELECT COALESCE(MAX(sort_order), -1) FROM participant_groups"
    ).fetchone()[0]
    gid = conn.execute(
        "INSERT INTO participant_groups (name, organisation_id, sort_order, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
        (name, organisation_id or None, max_order + 1, created_by, now()),
    ).lastrowid
    conn.commit()
    return gid


# ------------------------------------------------------ Organisations


def list_organisations(conn):
    """All organisations ordered by name."""
    return conn.execute("SELECT * FROM organisations ORDER BY name").fetchall()


def get_organisation(conn, org_id):
    return conn.execute("SELECT * FROM organisations WHERE id = ?", (org_id,)).fetchone()


def find_or_create_organisation(conn, name):
    """Find an organisation by name (case-insensitive) or create it. Returns org_id."""
    name = name.strip()
    row = conn.execute(
        "SELECT id FROM organisations WHERE lower(name) = lower(?)", (name,)
    ).fetchone()
    if row:
        return row["id"]
    oid = conn.execute(
        "INSERT INTO organisations (name, created_at) VALUES (?, ?)",
        (name, now()),
    ).lastrowid
    conn.commit()
    return oid


def add_organisation(conn, name, org_type=None, icon_url=None):
    name = name.strip()
    oid = conn.execute(
        "INSERT INTO organisations (name, type, icon_url, created_at) VALUES (?, ?, ?, ?)",
        (name, org_type or None, icon_url or None, now()),
    ).lastrowid
    conn.commit()
    return oid


def update_organisation(conn, org_id, name, org_type=None, icon_url=None):
    conn.execute(
        "UPDATE organisations SET name = ?, type = ?, icon_url = ? WHERE id = ?",
        (name.strip(), org_type or None, icon_url or None, org_id),
    )
    conn.commit()


def delete_organisation(conn, org_id):
    """Unlink groups and coaches from this org before deleting it."""
    conn.execute("UPDATE participant_groups SET organisation_id = NULL WHERE organisation_id = ?", (org_id,))
    conn.execute("UPDATE users SET organisation_id = NULL WHERE organisation_id = ?", (org_id,))
    conn.execute("DELETE FROM organisations WHERE id = ?", (org_id,))
    conn.commit()


def set_coach_organisation(conn, coach_id, org_id):  # kept for backward compat; coach_id = practitioner id
    conn.execute(
        "UPDATE users SET organisation_id = ? WHERE id = ? AND role IN ('practitioner','org_admin','system_admin')",
        (org_id or None, coach_id),
    )
    conn.commit()


def get_groups_for_org(conn, org_id):
    """All groups belonging to an organisation, ordered by sort_order."""
    return conn.execute(
        "SELECT * FROM participant_groups WHERE organisation_id = ? ORDER BY sort_order, id",
        (org_id,),
    ).fetchall()


def now():
    return datetime.datetime.utcnow().isoformat()


def today():
    return datetime.date.today().isoformat()


def is_seeded(conn):
    row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
    return row["c"] > 0


def seed_demo_data():
    """Populate the database with a coach account, demo participants, and a
    sample Measurement Games session for Alex.
    Safe to call repeatedly -- only seeds if the users table is empty."""
    conn = get_conn()
    try:
        if is_seeded(conn):
            return False

        # --- Coach / admin account -------------------------------------
        coach_id = conn.execute(
            "INSERT INTO users (name, email, password_hash, role, is_admin, sport, programme, created_at) "
            "VALUES (?, ?, ?, 'system_admin', 1, NULL, NULL, ?)",
            ("System Admin", "admin@justagame.co.nz", hash_password("CoachDemo123!"), now()),
        ).lastrowid

        # --- Demo participants ------------------------------------------
        participants = [
            ("Alex Taylor", "alex.demo@example.com", "Cricket",
             "Athlete Adaptability Programme - Masterton 2026"),
            ("Jess Nguyen", "jess.demo@example.com", "Football", "1-on-1 Coaching"),
            ("Sam Wilson", "sam.demo@example.com", "Hockey", "Small Group Coaching"),
        ]
        participant_ids = {}
        for name, email, sport, programme in participants:
            pid = conn.execute(
                "INSERT INTO users (name, email, password_hash, role, sport, programme, created_at) "
                "VALUES (?, ?, ?, 'participant', ?, ?, ?)",
                (name, email, hash_password("Athlete123!"), sport, programme, now()),
            ).lastrowid
            participant_ids[name] = pid

        # --- Sample Measurement Games session for Alex (demo) -----------
        alex = participant_ids["Alex Taylor"]
        mg_session_id = conn.execute(
            "INSERT INTO measurement_sessions (participant_id, date, logged_by, created_at) VALUES (?, ?, ?, ?)",
            (alex, "2026-06-23", coach_id, now()),
        ).lastrowid
        t1, t2, t3 = 5.21, 5.05, 4.98
        sample_results = [
            ("skipping_rope_sprint", "time_1", t1),
            ("skipping_rope_sprint", "time_2", t2),
            ("skipping_rope_sprint", "time_3", t3),
            ("skipping_rope_sprint", "average", round((t1 + t2 + t3) / 3, 2)),
            ("balance_ball_catching", "small_ball", 14),
            ("balance_ball_catching", "large_ball", 22),
            ("diamond_gates", "running_room", 8),
        ]
        for game_key, field_key, value in sample_results:
            conn.execute(
                "INSERT INTO measurement_results (session_id, game_key, field_key, value) VALUES (?, ?, ?, ?)",
                (mg_session_id, game_key, field_key, value),
            )

        conn.commit()
        return True
    finally:
        conn.close()


# ------------------------------------------------------ Measurement Games
# A "session" is one test day for one athlete; it can include results for
# any number of the games defined in constants.MEASUREMENT_GAMES (a coach
# doesn't have to fill in every game every time). Each individual field
# result is stored as its own row in measurement_results so the schema
# never needs to change if games/fields are added or removed later.


def create_measurement_session(conn, participant_id, date, logged_by, results, group_id=None,
                               session_label=None, session_month=None):
    """results: an iterable of (game_key, field_key, value) tuples, already
    filtered down to just the fields the coach actually filled in.
    group_id: the group the athlete belonged to at recording time (snapshot).
    session_label: e.g. 'baseline' or 'progress_1' (from SESSION_TYPES).
    session_month: YYYY-MM string; date is derived as YYYY-MM-01 if provided."""
    if session_month:
        date = session_month + "-01"
    session_id = conn.execute(
        "INSERT INTO measurement_sessions (participant_id, group_id, date, logged_by, created_at, session_label, session_month) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (participant_id, group_id, date, logged_by, now(), session_label, session_month),
    ).lastrowid
    for game_key, field_key, value in results:
        conn.execute(
            "INSERT INTO measurement_results (session_id, game_key, field_key, value) VALUES (?, ?, ?, ?)",
            (session_id, game_key, field_key, value),
        )
    conn.commit()
    return session_id


def measurement_sessions_for(conn, participant_id, group_id=None):
    """All Measurement Games sessions for a participant, most recent first.
    Pass group_id to restrict to sessions recorded while in that group
    (used by group-level pages so a transferred athlete's old data stays
    in the group they were in, not the new one).
    Pass group_id=None (default) to return all sessions — used for the
    athlete's own profile which shows their full history."""
    if group_id is not None:
        sessions = conn.execute(
            "SELECT * FROM measurement_sessions WHERE participant_id = ? AND group_id = ? ORDER BY date DESC, id DESC",
            (participant_id, group_id),
        ).fetchall()
    else:
        sessions = conn.execute(
            "SELECT * FROM measurement_sessions WHERE participant_id = ? ORDER BY date DESC, id DESC",
            (participant_id,),
        ).fetchall()
    out = []
    for s in sessions:
        rows = conn.execute(
            "SELECT game_key, field_key, value FROM measurement_results WHERE session_id = ?",
            (s["id"],),
        ).fetchall()
        out.append({
            "id": s["id"],
            "date": s["date"],
            "group_id": s["group_id"],
            "session_label": s.get("session_label"),
            "session_month": s.get("session_month"),
            "results": {(r["game_key"], r["field_key"]): r["value"] for r in rows},
        })
    return out


def count_measurement_sessions(conn, participant_id):
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM measurement_sessions WHERE participant_id = ?", (participant_id,)
    ).fetchone()
    return row["c"]


def delete_measurement_session(conn, session_id):
    conn.execute("DELETE FROM measurement_results WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM measurement_sessions WHERE id = ?", (session_id,))
    conn.commit()


def delete_participant(conn, participant_id):
    """Permanently delete a participant and all their associated data."""
    # measurement results → sessions
    ms_ids = [r["id"] for r in conn.execute(
        "SELECT id FROM measurement_sessions WHERE participant_id = ?", (participant_id,)
    ).fetchall()]
    for ms_id in ms_ids:
        conn.execute("DELETE FROM measurement_results WHERE session_id = ?", (ms_id,))
    conn.execute("DELETE FROM measurement_sessions WHERE participant_id = ?", (participant_id,))
    # awards
    conn.execute("DELETE FROM awards WHERE participant_id = ?", (participant_id,))
    # activity sessions (sessions table uses user_id, not participant_id)
    conn.execute("DELETE FROM sessions WHERE user_id = ?", (participant_id,))
    # user record
    conn.execute("DELETE FROM users WHERE id = ?", (participant_id,))
    conn.commit()


def merge_sessions_for_group(conn, group_id, target_label="baseline", target_month=None):
    """Merge all measurement sessions for each athlete in a group into a single session.

    For each athlete with multiple sessions in this group:
    - Keep the earliest session (by date, then id) as the target.
    - Copy measurement_results from all later sessions into the target,
      skipping any (game_key, field_key) pair that already exists in the target.
    - Update the target session's label and month to target_label / target_month.
    - Delete the extra sessions.

    Returns (athletes_merged, sessions_removed) counts.
    """
    athletes = conn.execute(
        "SELECT id FROM users WHERE group_id = ? AND role = 'participant'",
        (group_id,),
    ).fetchall()

    athletes_merged = 0
    sessions_removed = 0

    for athlete in athletes:
        pid = athlete["id"]
        sessions = conn.execute(
            "SELECT id FROM measurement_sessions "
            "WHERE participant_id = ? AND group_id = ? "
            "ORDER BY date ASC, id ASC",
            (pid, group_id),
        ).fetchall()

        if len(sessions) <= 1:
            # Nothing to merge; still relabel if there's exactly one
            if len(sessions) == 1:
                conn.execute(
                    "UPDATE measurement_sessions SET session_label = ?, session_month = ? WHERE id = ?",
                    (target_label, target_month, sessions[0]["id"]),
                )
            continue

        target_id = sessions[0]["id"]
        extra_ids = [s["id"] for s in sessions[1:]]

        # Build set of (game_key, field_key) already in target
        existing = set(
            (r["game_key"], r["field_key"])
            for r in conn.execute(
                "SELECT game_key, field_key FROM measurement_results WHERE session_id = ?",
                (target_id,),
            ).fetchall()
        )

        # Copy results from extra sessions that don't already exist in target
        for eid in extra_ids:
            rows = conn.execute(
                "SELECT game_key, field_key, value FROM measurement_results WHERE session_id = ?",
                (eid,),
            ).fetchall()
            for row in rows:
                key = (row["game_key"], row["field_key"])
                if key not in existing and row["value"] is not None:
                    conn.execute(
                        "INSERT INTO measurement_results (session_id, game_key, field_key, value) VALUES (?, ?, ?, ?)",
                        (target_id, row["game_key"], row["field_key"], row["value"]),
                    )
                    existing.add(key)
            # Delete extra session
            conn.execute("DELETE FROM measurement_results WHERE session_id = ?", (eid,))
            conn.execute("DELETE FROM measurement_sessions WHERE id = ?", (eid,))
            sessions_removed += 1

        # Relabel the surviving session
        conn.execute(
            "UPDATE measurement_sessions SET session_label = ?, session_month = ? WHERE id = ?",
            (target_label, target_month, target_id),
        )
        athletes_merged += 1

    conn.commit()
    return athletes_merged, sessions_removed


def relabel_unlabelled_sessions(conn, group_id, session_label, session_month):
    """Tag all unlabelled sessions for athletes in a group with a phase label and month.
    Only touches sessions that have no session_label yet.
    Where an athlete already has a labelled session for this label, their unlabelled
    sessions are left alone (to avoid creating a second labelled session for the same phase).
    Returns the number of sessions updated."""
    date = session_month + "-01" if session_month else None
    # Find all athletes in this group
    athletes = conn.execute(
        "SELECT id FROM users WHERE group_id = ? AND role = 'participant'", (group_id,)
    ).fetchall()
    updated = 0
    for athlete in athletes:
        pid = athlete["id"]
        # Skip if they already have a session with this label
        existing = conn.execute(
            "SELECT id FROM measurement_sessions WHERE participant_id = ? AND session_label = ?",
            (pid, session_label),
        ).fetchone()
        if existing:
            continue
        # Update their most recent unlabelled session
        rows = conn.execute(
            "UPDATE measurement_sessions SET session_label = ?, session_month = ?, date = COALESCE(?, date) "
            "WHERE participant_id = ? AND (session_label IS NULL OR session_label = '') "
            "ORDER BY id DESC LIMIT 1",
            (session_label, session_month, date, pid),
        )
        updated += rows.rowcount
    conn.commit()
    return updated


def find_session_by_label(conn, participant_id, session_label):
    """Return existing session dict for this athlete+label, or None."""
    return conn.execute(
        "SELECT * FROM measurement_sessions WHERE participant_id = ? AND session_label = ? ORDER BY id DESC LIMIT 1",
        (participant_id, session_label),
    ).fetchone()


def find_or_create_session(conn, participant_id, date, logged_by, group_id=None,
                           session_label=None, session_month=None):
    """Return the existing session id for this athlete+label (or date if no label), or create one.
    group_id is snapshotted on creation so the session stays attributed to
    the group the athlete was in at recording time."""
    if session_label:
        existing = conn.execute(
            "SELECT id FROM measurement_sessions WHERE participant_id = ? AND session_label = ? ORDER BY id DESC LIMIT 1",
            (participant_id, session_label),
        ).fetchone()
    else:
        existing = conn.execute(
            "SELECT id FROM measurement_sessions WHERE participant_id = ? AND date = ? ORDER BY id DESC LIMIT 1",
            (participant_id, date),
        ).fetchone()
    if existing:
        return existing["id"]
    return create_bare_session(conn, participant_id, date, logged_by, group_id=group_id,
                               session_label=session_label, session_month=session_month)


def create_bare_session(conn, participant_id, date, logged_by, group_id=None,
                        session_label=None, session_month=None):
    """Create a session with no results yet (used by quick-save flow)."""
    if session_month:
        date = session_month + "-01"
    session_id = conn.execute(
        "INSERT INTO measurement_sessions (participant_id, group_id, date, logged_by, created_at, session_label, session_month) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (participant_id, group_id, date, logged_by, now(), session_label, session_month),
    ).lastrowid
    conn.commit()
    return session_id


def upsert_measurement_result(conn, session_id, game_key, field_key, value):
    """Insert or update a single field result in an existing session."""
    existing = conn.execute(
        "SELECT id FROM measurement_results WHERE session_id = ? AND game_key = ? AND field_key = ?",
        (session_id, game_key, field_key),
    ).fetchone()
    if existing:
        conn.execute("UPDATE measurement_results SET value = ? WHERE id = ?", (value, existing["id"]))
    else:
        conn.execute(
            "INSERT INTO measurement_results (session_id, game_key, field_key, value) VALUES (?, ?, ?, ?)",
            (session_id, game_key, field_key, value),
        )
    conn.commit()


def update_password(conn, user_id, new_password):
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(new_password), user_id),
    )
    conn.commit()


def update_profile(conn, user_id, name, email, username=None):
    conn.execute(
        "UPDATE users SET name = ?, email = ?, username = ? WHERE id = ?",
        (name, email, username or None, user_id),
    )
    conn.commit()


def list_coaches(conn):
    """Return all staff accounts (practitioner, org_admin, system_admin)."""
    return conn.execute(
        "SELECT * FROM users WHERE role IN ('practitioner','org_admin','system_admin') ORDER BY name"
    ).fetchall()


def set_role(conn, user_id, role):
    """Set a staff user's role. role must be one of practitioner/org_admin/system_admin."""
    valid = {"practitioner", "org_admin", "system_admin"}
    if role not in valid:
        raise ValueError(f"Invalid role: {role!r}. Must be one of {valid}")
    conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    conn.commit()


def set_admin_status(conn, user_id, is_admin):
    """Legacy helper — promotes to system_admin or demotes to practitioner."""
    new_role = "system_admin" if is_admin else "practitioner"
    conn.execute("UPDATE users SET role = ?, is_admin = ? WHERE id = ?",
                 (new_role, 1 if is_admin else 0, user_id))
    conn.commit()


def get_coach_group_ids(conn, coach_id):
    """Return list of group_ids assigned to a coach (from coach_groups junction table)."""
    rows = conn.execute(
        "SELECT group_id FROM coach_groups WHERE coach_id = ?", (coach_id,)
    ).fetchall()
    return [r["group_id"] for r in rows]


def set_coach_groups(conn, coach_id, group_ids):
    """Replace all group assignments for a coach. group_ids is a list of ints (may be empty)."""
    conn.execute("DELETE FROM coach_groups WHERE coach_id = ?", (coach_id,))
    for gid in group_ids:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO coach_groups (coach_id, group_id) VALUES (?, ?)",
                (coach_id, int(gid)),
            )
        except Exception:
            pass
    conn.commit()


def set_active(conn, user_id, active):
    conn.execute("UPDATE users SET active = ? WHERE id = ?", (1 if active else 0, user_id))
    conn.commit()


# ------------------------------------------------------ Participant Groups


def list_participant_groups(conn):
    return conn.execute(
        "SELECT * FROM participant_groups ORDER BY sort_order, id"
    ).fetchall()


def add_participant_group(conn, name, created_by, icon_url=None):
    max_order = conn.execute("SELECT COALESCE(MAX(sort_order), -1) FROM participant_groups").fetchone()[0]
    conn.execute(
        "INSERT INTO participant_groups (name, icon_url, sort_order, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
        (name, icon_url or None, max_order + 1, created_by, now()),
    )
    conn.commit()


def update_participant_group(conn, group_id, name, icon_url=None, show_leaderboard=0):
    conn.execute(
        "UPDATE participant_groups SET name = ?, icon_url = ?, show_leaderboard = ? WHERE id = ?",
        (name, icon_url or None, int(bool(show_leaderboard)), group_id),
    )
    conn.commit()


def delete_participant_group(conn, group_id):
    # Move participants in this group to ungrouped rather than removing them
    conn.execute("UPDATE users SET group_id = NULL WHERE group_id = ?", (group_id,))
    # Remove coach-group assignments (FK constraint would block the delete otherwise)
    conn.execute("DELETE FROM coach_groups WHERE group_id = ?", (group_id,))
    # Unlink measurement sessions (keep the data, just remove the group snapshot)
    conn.execute("UPDATE measurement_sessions SET group_id = NULL WHERE group_id = ?", (group_id,))
    conn.execute("DELETE FROM participant_groups WHERE id = ?", (group_id,))
    conn.commit()


def assign_participant_group(conn, participant_id, group_id):
    """Set group_id for a participant. Pass None to remove from all groups."""
    conn.execute(
        "UPDATE users SET group_id = ? WHERE id = ?",
        (group_id or None, participant_id),
    )
    conn.commit()


def list_participants_by_group(conn, organisation_id=None):
    """Returns (group_groups, ungrouped) where group_groups is a list of
    (group_row, [participant_rows]) tuples ordered by group sort_order.
    Pass organisation_id to restrict to groups belonging to that organisation."""
    if organisation_id is not None:
        groups = conn.execute(
            "SELECT * FROM participant_groups WHERE organisation_id = ? ORDER BY sort_order, id",
            (organisation_id,),
        ).fetchall()
    else:
        groups = list_participant_groups(conn)
    all_participants = conn.execute(
        "SELECT * FROM users WHERE role = 'participant' AND active = 1 ORDER BY name"
    ).fetchall()
    group_ids = {g["id"] for g in groups}
    by_group = {}
    ungrouped = []
    for p in all_participants:
        gid = p["group_id"]
        if gid is None or (organisation_id is not None and gid not in group_ids):
            if organisation_id is None:
                ungrouped.append(p)
        else:
            by_group.setdefault(gid, []).append(p)
    if organisation_id is None:
        pass  # ungrouped already populated above
    group_groups = [(g, by_group.get(g["id"], [])) for g in groups]
    return group_groups, ungrouped


# ------------------------------------------------------ Resource Folders


def list_folders(conn):
    return conn.execute(
        "SELECT * FROM resource_folders ORDER BY sort_order, id"
    ).fetchall()


def add_folder(conn, name, created_by):
    max_order = conn.execute("SELECT COALESCE(MAX(sort_order), -1) FROM resource_folders").fetchone()[0]
    conn.execute(
        "INSERT INTO resource_folders (name, sort_order, created_by, created_at) VALUES (?, ?, ?, ?)",
        (name, max_order + 1, created_by, now()),
    )
    conn.commit()


def rename_folder(conn, folder_id, name):
    conn.execute("UPDATE resource_folders SET name = ? WHERE id = ?", (name, folder_id))
    conn.commit()


def delete_folder(conn, folder_id):
    # Move resources in this folder to ungrouped rather than deleting them
    conn.execute("UPDATE resources SET folder_id = NULL WHERE folder_id = ?", (folder_id,))
    conn.execute("DELETE FROM resource_folders WHERE id = ?", (folder_id,))
    conn.commit()


def list_resources_by_folder(conn):
    """Returns (folder_groups, ungrouped) where folder_groups is a list of
    (folder_row, [resource_rows]) tuples ordered by folder sort_order."""
    folders = list_folders(conn)
    all_resources = conn.execute(
        "SELECT r.*, u.name AS added_by_name FROM resources r "
        "LEFT JOIN users u ON u.id = r.added_by ORDER BY r.sort_order, r.id"
    ).fetchall()
    by_folder = {}
    ungrouped = []
    for r in all_resources:
        fid = r["folder_id"]
        if fid is None:
            ungrouped.append(r)
        else:
            by_folder.setdefault(fid, []).append(r)
    folder_groups = [(f, by_folder.get(f["id"], [])) for f in folders]
    return folder_groups, ungrouped


def add_resource(conn, name, description, url, added_by, folder_id=None):
    max_order = conn.execute("SELECT COALESCE(MAX(sort_order), -1) FROM resources").fetchone()[0]
    conn.execute(
        "INSERT INTO resources (name, description, url, added_by, folder_id, sort_order, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, description or None, url, added_by, folder_id or None, max_order + 1, now()),
    )
    conn.commit()


def move_resource(conn, resource_id, folder_id):
    """Move a resource to a different folder (or ungrouped if folder_id is None)."""
    conn.execute(
        "UPDATE resources SET folder_id = ? WHERE id = ?",
        (folder_id or None, resource_id),
    )
    conn.commit()


def update_resource(conn, resource_id, name, description, url, folder_id,
                    self_organisation=None, level_range="multi_level",
                    space_requirement="unspecified", card_slug=None):
    conn.execute(
        "UPDATE resources SET name = ?, description = ?, url = ?, folder_id = ?, "
        "self_organisation = ?, level_range = ?, space_requirement = ?, card_slug = ? WHERE id = ?",
        (name, description or None, url, folder_id or None,
         self_organisation or None, level_range or "multi_level",
         space_requirement or "unspecified", card_slug or None, resource_id),
    )
    conn.commit()


def delete_resource(conn, resource_id):
    conn.execute("DELETE FROM resources WHERE id = ?", (resource_id,))
    conn.commit()


# ---- Resource tags --------------------------------------------------------

def list_tags(conn):
    return conn.execute("SELECT * FROM resource_tags ORDER BY sort_order, name").fetchall()


def add_tag(conn, name):
    max_order = conn.execute("SELECT COALESCE(MAX(sort_order), -1) FROM resource_tags").fetchone()[0]
    conn.execute(
        "INSERT INTO resource_tags (name, sort_order, created_at) VALUES (?, ?, ?)",
        (name.strip(), max_order + 1, now()),
    )
    conn.commit()


def delete_tag(conn, tag_id):
    conn.execute("DELETE FROM resource_tags WHERE id = ?", (tag_id,))
    conn.commit()


def get_resource_tag_ids(conn, resource_id):
    rows = conn.execute(
        "SELECT tag_id FROM resource_tag_assignments WHERE resource_id = ?", (resource_id,)
    ).fetchall()
    return [r["tag_id"] for r in rows]


def set_resource_tags(conn, resource_id, tag_ids):
    """Replace all tag assignments for a resource."""
    conn.execute("DELETE FROM resource_tag_assignments WHERE resource_id = ?", (resource_id,))
    for tid in tag_ids:
        conn.execute(
            "INSERT INTO resource_tag_assignments (resource_id, tag_id) VALUES (?, ?)",
            (resource_id, tid),
        )
    conn.commit()


# ── Resource game-key taxonomy (hidden structural tags) ───────────────────

def get_resource_game_keys(conn, resource_id):
    """Return list of game_key strings linked to this resource."""
    rows = conn.execute(
        "SELECT game_key FROM resource_game_links WHERE resource_id = ? ORDER BY game_key",
        (resource_id,),
    ).fetchall()
    return [r["game_key"] for r in rows]


def set_resource_game_keys(conn, resource_id, game_keys):
    """Replace all game_key links for a resource (idempotent)."""
    conn.execute("DELETE FROM resource_game_links WHERE resource_id = ?", (resource_id,))
    for gk in game_keys:
        if gk:
            conn.execute(
                "INSERT OR IGNORE INTO resource_game_links (resource_id, game_key) VALUES (?, ?)",
                (resource_id, gk),
            )
    conn.commit()


def sync_card_taxonomy(conn, resource_id=None):
    """Apply CARD_TAXONOMY tags to resources that have a card_slug set.

    If resource_id is given, only that resource is synced.
    Returns (updated, skipped, errors) tuple.
    """
    from constants import CARD_TAXONOMY
    if resource_id:
        rows = conn.execute(
            "SELECT id, card_slug FROM resources WHERE id = ? AND card_slug IS NOT NULL",
            (resource_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, card_slug FROM resources WHERE card_slug IS NOT NULL"
        ).fetchall()
    updated, skipped, errors = 0, 0, []
    for row in rows:
        rid = row["id"]
        slug = row["card_slug"]
        taxonomy = CARD_TAXONOMY.get(slug)
        if not taxonomy:
            skipped += 1
            errors.append(f"No CARD_TAXONOMY entry for slug '{slug}' (resource {rid})")
            continue
        try:
            game_keys = taxonomy.get("game_keys", [])
            dim_tags = {k: v for k, v in taxonomy.items() if k != "game_keys"}
            set_resource_game_keys(conn, rid, game_keys)
            set_resource_taxonomy_tags(conn, rid, dim_tags)
            updated += 1
        except Exception as exc:
            errors.append(f"Error syncing resource {rid}: {exc}")
    return updated, skipped, errors


def get_resource_taxonomy_tags(conn, resource_id):
    """Return {dimension: [value, ...]} for a resource's taxonomy tags."""
    rows = conn.execute(
        "SELECT dimension, value FROM resource_taxonomy_tags WHERE resource_id = ? ORDER BY dimension, value",
        (resource_id,),
    ).fetchall()
    result = {}
    for r in rows:
        result.setdefault(r["dimension"], []).append(r["value"])
    return result


def set_resource_taxonomy_tags(conn, resource_id, tags_by_dimension):
    """Replace all taxonomy tags for a resource (idempotent).

    tags_by_dimension: {dimension: [value, ...]}  e.g. {'D1': ['balance_postural'], 'D2': [...]}
    """
    conn.execute("DELETE FROM resource_taxonomy_tags WHERE resource_id = ?", (resource_id,))
    for dimension, values in tags_by_dimension.items():
        for value in values:
            if value:
                conn.execute(
                    "INSERT OR IGNORE INTO resource_taxonomy_tags (resource_id, dimension, value) VALUES (?, ?, ?)",
                    (resource_id, dimension, value),
                )
    conn.commit()


def get_game_keys_for_resources(conn, resource_ids):
    """Return {resource_id: [game_key, ...]} for a list of resource IDs."""
    if not resource_ids:
        return {}
    placeholders = ",".join("?" * len(resource_ids))
    rows = conn.execute(
        f"SELECT resource_id, game_key FROM resource_game_links WHERE resource_id IN ({placeholders})",
        resource_ids,
    ).fetchall()
    result = {rid: [] for rid in resource_ids}
    for r in rows:
        result[r["resource_id"]].append(r["game_key"])
    return result


def get_recommended_resources(conn, participant_id, limit=6):
    """Return resources matched to an athlete's current gaps.

    Scoring (per taxonomy doc):
      - D10 match (game_key link):   3 pts per resource
      - D2/D3 match (taxonomy tags): 2 pts each  (future — once resources are tagged)
      - D1 match (family):           1 pt each    (future)
      - Filter: level_range must match athlete's level or be 'multi_level'

    Current implementation: D10 + level_range filter, priority-ordered by
    most-needed game first. D2/D3 scoring is wired in once resources carry
    full taxonomy tags.
    """
    from constants import CORE_AAP_GAMES
    levels = get_all_athlete_levels(conn, participant_id)

    # Athlete level → resource level_range needed
    # 0 (no level) → Level 1 resources  |  1 → Level 2  |  2+ → Level 3
    RANGE_MAP = {0: "level_1", 1: "level_2"}  # default → "level_3"

    # Sort games: unachieved levels first (biggest gap = highest priority)
    game_priority = []
    for gk in CORE_AAP_GAMES:
        lvl = levels.get(gk, 0)
        needed = RANGE_MAP.get(lvl, "level_3")
        game_priority.append((gk, needed, lvl))
    game_priority.sort(key=lambda x: x[2])  # lowest level = most needed

    seen_ids = set()
    results = []
    for gk, needed_range, _lvl in game_priority:
        rows = conn.execute(
            """SELECT r.* FROM resources r
               JOIN resource_game_links rgl ON rgl.resource_id = r.id
               WHERE rgl.game_key = ?
                 AND (r.level_range = ? OR r.level_range = 'multi_level')
               ORDER BY r.sort_order, r.name""",
            (gk, needed_range),
        ).fetchall()
        for row in rows:
            if row["id"] not in seen_ids:
                seen_ids.add(row["id"])
                results.append(dict(row))
                if len(results) >= limit:
                    return results
    return results


def get_tags_for_resources(conn, resource_ids):
    """Returns dict {resource_id: [tag_row, ...]} for a list of resource IDs."""
    if not resource_ids:
        return {}
    placeholders = ",".join("?" * len(resource_ids))
    rows = conn.execute(
        f"SELECT rta.resource_id, rt.id, rt.name FROM resource_tag_assignments rta "
        f"JOIN resource_tags rt ON rt.id = rta.tag_id "
        f"WHERE rta.resource_id IN ({placeholders}) ORDER BY rt.name",
        resource_ids,
    ).fetchall()
    result = {rid: [] for rid in resource_ids}
    for r in rows:
        result[r["resource_id"]].append(r)
    return result


def reorder_items(conn, table, ordered_ids):
    """Set sort_order = index position for each id in the list."""
    for i, item_id in enumerate(ordered_ids):
        conn.execute(f"UPDATE {table} SET sort_order = ? WHERE id = ?", (i, item_id))
    conn.commit()


# ══════════════════════════════════════════════════════════════════════════════
# XP ENGINE
# All XP logic lives here so the rest of the app just calls process_session_xp.
# ══════════════════════════════════════════════════════════════════════════════

def _import_xp_constants():
    """Lazy import to avoid circular imports at module load time."""
    from constants import (
        XP_GAME_CONFIG, LEVEL_XP_AWARDS, XP_RANK_TIERS,
        XP_PARTICIPATION, CORE_AAP_GAMES,
    )
    return XP_GAME_CONFIG, LEVEL_XP_AWARDS, XP_RANK_TIERS, XP_PARTICIPATION, CORE_AAP_GAMES


# ── Ledger ────────────────────────────────────────────────────────────────────

def award_xp(conn, participant_id, xp_type, amount, game_key=None,
             session_id=None, notes=None):
    """Append one XP event to the ledger. Returns the new event id."""
    eid = conn.execute(
        "INSERT INTO xp_events (participant_id, xp_type, amount, game_key, session_id, notes, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (participant_id, xp_type, amount, game_key, session_id, notes, now()),
    ).lastrowid
    conn.commit()
    return eid


def get_athlete_xp(conn, participant_id):
    """Return dict with total XP, rank tier, next tier, and recent events."""
    XP_GAME_CONFIG, LEVEL_XP_AWARDS, XP_RANK_TIERS, XP_PARTICIPATION, CORE_AAP_GAMES = _import_xp_constants()
    from constants import get_athlete_rank_tier, get_next_rank_tier

    total_row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM xp_events WHERE participant_id = ?",
        (participant_id,),
    ).fetchone()
    total = int(total_row["total"])

    events = conn.execute(
        "SELECT * FROM xp_events WHERE participant_id = ? ORDER BY id DESC LIMIT 50",
        (participant_id,),
    ).fetchall()

    tier = get_athlete_rank_tier(total)
    next_tier = get_next_rank_tier(total)

    # Progress to next tier (0.0 – 1.0)
    if next_tier:
        span = next_tier["min_xp"] - tier["min_xp"]
        into = total - tier["min_xp"]
        progress = min(1.0, into / span) if span else 1.0
    else:
        progress = 1.0

    return {
        "total": total,
        "tier": tier,
        "next_tier": next_tier,
        "progress": progress,
        "events": [dict(e) for e in events],
    }


def xp_total_for(conn, participant_id):
    """Lightweight: return just the total XP integer."""
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM xp_events WHERE participant_id = ?",
        (participant_id,),
    ).fetchone()
    return int(row["total"])


# ── Personal Bests ────────────────────────────────────────────────────────────

def get_personal_best(conn, participant_id, game_key, field_key):
    """Return the current PB row or None."""
    return conn.execute(
        "SELECT * FROM athlete_personal_bests WHERE participant_id = ? AND game_key = ? AND field_key = ?",
        (participant_id, game_key, field_key),
    ).fetchone()


def update_personal_best(conn, participant_id, game_key, field_key, value,
                         session_id=None, is_formal=True):
    """Upsert a PB. Returns (is_new_pb: bool, improvement: float or None).
    improvement is None for the first record, else the delta (positive = better)."""
    existing = get_personal_best(conn, participant_id, game_key, field_key)
    XP_GAME_CONFIG = _import_xp_constants()[0]
    cfg = XP_GAME_CONFIG.get(game_key, {})
    lower_is_better = cfg.get("lower_is_better", False)

    if existing is None:
        # First ever score for this game/field — always a PB
        conn.execute(
            "INSERT INTO athlete_personal_bests "
            "(participant_id, game_key, field_key, best_value, session_id, is_formal, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (participant_id, game_key, field_key, value, session_id, 1 if is_formal else 0, now()),
        )
        conn.commit()
        return True, None  # first record — no improvement delta yet

    old = existing["best_value"]
    if lower_is_better:
        is_pb = value < old
        improvement = old - value  # positive = faster
    else:
        is_pb = value > old
        improvement = value - old  # positive = more

    if is_pb:
        conn.execute(
            "UPDATE athlete_personal_bests SET best_value = ?, session_id = ?, is_formal = ?, updated_at = ? "
            "WHERE participant_id = ? AND game_key = ? AND field_key = ?",
            (value, session_id, 1 if is_formal else 0, now(), participant_id, game_key, field_key),
        )
        conn.commit()

    return is_pb, improvement if is_pb else None


# ── Level Achievements ────────────────────────────────────────────────────────

def get_athlete_level(conn, participant_id, game_key, field_key=""):
    """Return the highest level the athlete has earned for a scoring area, or 0.
    field_key="" means a game-level achievement (most games).
    Pass the specific field_key for Balance Ball Two Feet / One Foot."""
    row = conn.execute(
        "SELECT MAX(level) AS lvl FROM level_achievements "
        "WHERE participant_id = ? AND game_key = ? AND field_key = ?",
        (participant_id, game_key, field_key),
    ).fetchone()
    return row["lvl"] or 0


def get_all_athlete_levels(conn, participant_id):
    """Return dict {game_key: highest_level} for all games this athlete has levels in.
    For games with multiple scoring areas (Balance Ball), returns the max across all areas.
    Backward-compatible format for all existing callers that key by game_key only."""
    rows = conn.execute(
        "SELECT game_key, MAX(level) AS lvl FROM level_achievements "
        "WHERE participant_id = ? GROUP BY game_key",
        (participant_id,),
    ).fetchall()
    return {r["game_key"]: r["lvl"] for r in rows}


def get_all_athlete_levels_by_area(conn, participant_id):
    """Return dict keyed by (game_key, field_key) → highest level.
    Use this for the per-scoring-area level grid (Balance Ball has two separate entries)."""
    rows = conn.execute(
        "SELECT game_key, field_key, MAX(level) AS lvl FROM level_achievements "
        "WHERE participant_id = ? GROUP BY game_key, field_key",
        (participant_id,),
    ).fetchall()
    return {(r["game_key"], r["field_key"] or ""): r["lvl"] for r in rows}


def get_group_athletes_with_levels(conn, group_id):
    """Return list of athlete dicts each with a 'levels' sub-dict keyed by (game_key, field_key).
    Used for group-level analysis (Next Steps report)."""
    athletes = conn.execute(
        "SELECT id, name, athlete_number, sport FROM users "
        "WHERE group_id = ? AND role = 'participant' ORDER BY name",
        (group_id,),
    ).fetchall()
    result = []
    for a in athletes:
        levels = get_all_athlete_levels_by_area(conn, a["id"])
        result.append({"id": a["id"], "name": a["name"],
                       "athlete_number": a["athlete_number"],
                       "sport": a["sport"], "levels": levels})
    return result


def award_level(conn, participant_id, game_key, level, field_key="", session_id=None):
    """Award a level to an athlete for a specific scoring area.
    Idempotent (UNIQUE constraint, silently skips duplicates).
    Returns True if a new level was awarded, False if already held.
    field_key="" for standard games; specific field_key for multi-field games (Balance Ball)."""
    try:
        conn.execute(
            "INSERT INTO level_achievements "
            "(participant_id, game_key, field_key, level, session_id, awarded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (participant_id, game_key, field_key, level, session_id, now()),
        )
        conn.commit()
        return True
    except Exception:
        return False


# ── Level Thresholds ──────────────────────────────────────────────────────────

# ── Testing Round Helpers ─────────────────────────────────────────────────────

def get_available_round_options(conn, group_id):
    """Return a list of dicts describing what round types the group can open next.
    Rules:
    - Only one round may be open at a time.
    - If any round is open, returns [].
    - Level 1 Baseline is always available if never done.
    - Re-Test requires the same level's Baseline to be closed.
    - Level N Baseline requires Level N-1 Re-Test (at least one) to be closed.
    - Multiple Re-Tests at same level are allowed before advancing.
    """
    open_round = conn.execute(
        "SELECT id FROM testing_rounds WHERE group_id = ? AND status = 'open'", (group_id,)
    ).fetchone()
    if open_round:
        return []

    closed = conn.execute(
        "SELECT level, round_type FROM testing_rounds "
        "WHERE group_id = ? AND status = 'closed' ORDER BY id",
        (group_id,),
    ).fetchall()

    done_baselines = {r["level"] for r in closed if r["round_type"] == "baseline"}
    done_retests   = {r["level"] for r in closed if r["round_type"] == "retest"}

    options = []

    # Level 1 Baseline always available if not yet done
    if 1 not in done_baselines:
        options.append({"level": 1, "round_type": "baseline", "label": "Level 1 Baseline"})
        return options  # nothing else can happen until L1 baseline is done

    # For each level: if baseline done but no retest → retest is the only option
    # If retest done → can do another retest OR next level's baseline
    for lvl in range(1, 6):
        if lvl not in done_baselines:
            break
        if lvl not in done_retests:
            # Must complete retest before anything else
            options.append({"level": lvl, "round_type": "retest", "label": f"Level {lvl} Re-Test"})
            return options
        else:
            # Can repeat retest at this level
            options.append({"level": lvl, "round_type": "retest", "label": f"Level {lvl} Re-Test"})
            # Or advance to next level baseline (if not already done and level exists)
            next_lvl = lvl + 1
            if next_lvl <= 5 and next_lvl not in done_baselines:
                options.append({"level": next_lvl, "round_type": "baseline",
                                "label": f"Level {next_lvl} Baseline"})

    return options


def open_testing_round(conn, group_id, level, round_type, opened_by):
    """Open a new testing round for a group. Validates unlock rules.
    Returns (round_id, None) on success or (None, error_message) on failure."""
    available = get_available_round_options(conn, group_id)
    if not available:
        return None, "A round is already open for this group, or no rounds are available."
    valid = any(o["level"] == level and o["round_type"] == round_type for o in available)
    if not valid:
        return None, f"Level {level} {round_type} is not available for this group yet."

    # Calculate retest_sequence
    retest_sequence = None
    if round_type == "retest":
        existing = conn.execute(
            "SELECT COUNT(*) AS cnt FROM testing_rounds "
            "WHERE group_id = ? AND level = ? AND round_type = 'retest'",
            (group_id, level),
        ).fetchone()
        retest_sequence = (existing["cnt"] or 0) + 1

    conn.execute(
        "INSERT INTO testing_rounds (group_id, level, round_type, retest_sequence, "
        "status, opened_at, opened_by) VALUES (?, ?, ?, ?, 'open', ?, ?)",
        (group_id, level, round_type, retest_sequence, now(), opened_by),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM testing_rounds WHERE group_id = ? ORDER BY id DESC LIMIT 1", (group_id,)
    ).fetchone()
    return row["id"], None


def get_testing_round(conn, round_id):
    return conn.execute(
        "SELECT tr.*, pg.name AS group_name FROM testing_rounds tr "
        "JOIN participant_groups pg ON pg.id = tr.group_id "
        "WHERE tr.id = ?", (round_id,)
    ).fetchone()


def get_open_round_for_group(conn, group_id):
    return conn.execute(
        "SELECT * FROM testing_rounds WHERE group_id = ? AND status = 'open' "
        "ORDER BY opened_at DESC LIMIT 1", (group_id,)
    ).fetchone()


def get_rounds_for_group(conn, group_id):
    return conn.execute(
        "SELECT * FROM testing_rounds WHERE group_id = ? ORDER BY id DESC", (group_id,)
    ).fetchall()


def upsert_round_score(conn, round_id, athlete_id, game_key, field_key, value, recorded_by):
    """Insert or update a single score field for an athlete in a round."""
    existing = conn.execute(
        "SELECT id FROM round_scores WHERE round_id = ? AND athlete_id = ? "
        "AND game_key = ? AND field_key = ?",
        (round_id, athlete_id, game_key, field_key),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE round_scores SET value = ?, recorded_at = ?, recorded_by = ? WHERE id = ?",
            (value, now(), recorded_by, existing["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO round_scores (round_id, athlete_id, game_key, field_key, "
            "value, recorded_at, recorded_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (round_id, athlete_id, game_key, field_key, value, now(), recorded_by),
        )
    conn.commit()


def get_round_scores(conn, round_id):
    """Return all score rows for a round."""
    return conn.execute(
        "SELECT rs.*, u.name AS athlete_name FROM round_scores rs "
        "JOIN users u ON u.id = rs.athlete_id WHERE rs.round_id = ? "
        "ORDER BY u.name, rs.game_key, rs.field_key",
        (round_id,),
    ).fetchall()


def get_athlete_round_scores(conn, round_id, athlete_id):
    """Return scores for one athlete in a round as {game_key: {field_key: value}}."""
    rows = conn.execute(
        "SELECT game_key, field_key, value FROM round_scores "
        "WHERE round_id = ? AND athlete_id = ?",
        (round_id, athlete_id),
    ).fetchall()
    result = {}
    for r in rows:
        result.setdefault(r["game_key"], {})[r["field_key"]] = r["value"]
    return result


def get_previous_round_for_comparison(conn, round_id):
    """Return the round that should be used as the comparison baseline for this round.
    For retest_sequence=1: compare to the baseline round at the same level.
    For retest_sequence=2+: compare to the previous retest at the same level.
    Returns None for baseline rounds (no comparison possible).
    """
    rnd = conn.execute("SELECT * FROM testing_rounds WHERE id = ?", (round_id,)).fetchone()
    if not rnd or rnd["round_type"] == "baseline":
        return None
    group_id = rnd["group_id"]
    level    = rnd["level"]
    seq      = rnd["retest_sequence"] or 1

    if seq == 1:
        # Compare to the baseline at this level
        return conn.execute(
            "SELECT * FROM testing_rounds WHERE group_id = ? AND level = ? "
            "AND round_type = 'baseline' AND status = 'closed' ORDER BY id DESC LIMIT 1",
            (group_id, level),
        ).fetchone()
    else:
        # Compare to previous retest at this level
        return conn.execute(
            "SELECT * FROM testing_rounds WHERE group_id = ? AND level = ? "
            "AND round_type = 'retest' AND retest_sequence = ? AND status = 'closed' ORDER BY id DESC LIMIT 1",
            (group_id, level, seq - 1),
        ).fetchone()


def close_testing_round(conn, round_id):
    """Close a testing round and calculate + award AXP for all athletes.
    Returns list of {athlete_id, athlete_name, total_xp} dicts.
    """
    from constants import (
        XP_GAME_CONFIG, CORE_AAP_GAMES,
        ROUND_XP_LEVEL_TIERS, ROUND_XP_COMPLETION_BONUS,
        ROUND_XP_BASELINE_PER_GAME, ROUND_XP_IMPROVEMENT_FACTOR, ROUND_XP_IMPROVEMENT_CAP,
    )
    rnd = conn.execute("SELECT * FROM testing_rounds WHERE id = ?", (round_id,)).fetchone()
    if not rnd:
        return []
    is_baseline   = (rnd["round_type"] == "baseline")
    prev_round    = None if is_baseline else get_previous_round_for_comparison(conn, round_id)
    group_id      = rnd["group_id"]
    ts            = now()

    # Gather all athletes in this group
    athletes = conn.execute(
        "SELECT u.id, u.name FROM users u "
        "JOIN participant_groups pg ON pg.id = ? "
        "WHERE u.group_id = ? AND u.role = 'participant' AND u.active = 1",
        (group_id, group_id),
    ).fetchall()
    # Fallback: get athletes from round_scores if group membership query returns nothing
    if not athletes:
        athletes = conn.execute(
            "SELECT DISTINCT u.id, u.name FROM users u "
            "JOIN round_scores rs ON rs.athlete_id = u.id WHERE rs.round_id = ?",
            (round_id,),
        ).fetchall()

    # Resolve the AXP tier for this round's level (fallback to L1 defaults)
    round_level = rnd.get("level") or 1
    _tier        = ROUND_XP_LEVEL_TIERS.get(round_level, ROUND_XP_LEVEL_TIERS.get(1, {}))
    _factor      = _tier.get("factor",      ROUND_XP_IMPROVEMENT_FACTOR)
    _cap         = _tier.get("cap",         ROUND_XP_IMPROVEMENT_CAP)
    _baseline_xp = _tier.get("baseline_xp", ROUND_XP_BASELINE_PER_GAME)

    summaries = []
    for athlete in athletes:
        aid   = athlete["id"]
        aname = athlete["name"]
        scores_this  = get_athlete_round_scores(conn, round_id, aid)
        scores_prev  = {} if not prev_round else get_athlete_round_scores(conn, prev_round["id"], aid)
        total_xp     = 0
        games_scored = 0

        for game_key in CORE_AAP_GAMES:
            cfg = XP_GAME_CONFIG.get(game_key, {})
            primary_field     = cfg.get("primary_field")
            higher_is_better  = cfg.get("higher_is_better", True)
            this_game         = scores_this.get(game_key, {})
            score_this        = this_game.get(primary_field) if primary_field else None

            if score_this is None:
                continue
            try:
                score_this = float(score_this)
            except (TypeError, ValueError):
                continue

            games_scored += 1

            if is_baseline:
                xp = _baseline_xp
                conn.execute(
                    "INSERT INTO round_xp_awards (round_id, athlete_id, game_key, "
                    "improvement_pct, xp_awarded, award_type, awarded_at) VALUES (?,?,?,NULL,?,?,?)",
                    (round_id, aid, game_key, xp, "baseline_participation", ts),
                )
                conn.execute(
                    "INSERT INTO xp_events (participant_id, xp_type, amount, game_key, notes, created_at) "
                    "VALUES (?, 'round_baseline', ?, ?, ?, ?)",
                    (aid, xp, game_key, f"Baseline round Level {rnd['level']}", ts),
                )
                total_xp += xp
            else:
                prev_game  = scores_prev.get(game_key, {})
                score_prev = prev_game.get(primary_field) if primary_field else None
                if score_prev is None:
                    continue
                try:
                    score_prev = float(score_prev)
                except (TypeError, ValueError):
                    continue
                if score_prev == 0:
                    improvement_pct = 0.0
                elif higher_is_better:
                    improvement_pct = max(0.0, (score_this - score_prev) / score_prev * 100)
                else:
                    improvement_pct = max(0.0, (score_prev - score_this) / score_prev * 100)

                xp = min(int(improvement_pct * _factor), _cap)
                conn.execute(
                    "INSERT INTO round_xp_awards (round_id, athlete_id, game_key, "
                    "improvement_pct, xp_awarded, award_type, awarded_at) VALUES (?,?,?,?,?,?,?)",
                    (round_id, aid, game_key, round(improvement_pct, 2), xp, "improvement", ts),
                )
                if xp > 0:
                    conn.execute(
                        "INSERT INTO xp_events (participant_id, xp_type, amount, game_key, notes, created_at) "
                        "VALUES (?, 'round_improvement', ?, ?, ?, ?)",
                        (aid, xp, game_key,
                         f"Level {rnd['level']} Re-Test {rnd['retest_sequence']} — "
                         f"{round(improvement_pct,1)}% improvement", ts),
                    )
                total_xp += xp

        # Completion bonus: all 8 core games scored
        if games_scored >= len(CORE_AAP_GAMES):
            bonus = ROUND_XP_COMPLETION_BONUS
            conn.execute(
                "INSERT INTO round_xp_awards (round_id, athlete_id, game_key, "
                "improvement_pct, xp_awarded, award_type, awarded_at) VALUES (?,?,NULL,NULL,?,?,?)",
                (round_id, aid, bonus, "completion_bonus", ts),
            )
            conn.execute(
                "INSERT INTO xp_events (participant_id, xp_type, amount, game_key, notes, created_at) "
                "VALUES (?, 'round_completion', ?, NULL, ?, ?)",
                (aid, bonus, f"Completed all games — Level {rnd['level']} round", ts),
            )
            total_xp += bonus

        summaries.append({"athlete_id": aid, "athlete_name": aname, "total_xp": total_xp})

    conn.execute(
        "UPDATE testing_rounds SET status = 'closed', closed_at = ? WHERE id = ?",
        (ts, round_id),
    )
    conn.commit()
    return summaries


def get_round_xp_summary(conn, round_id, athlete_id):
    """Return AXP award rows for one athlete in a round."""
    return conn.execute(
        "SELECT * FROM round_xp_awards WHERE round_id = ? AND athlete_id = ? ORDER BY id",
        (round_id, athlete_id),
    ).fetchall()


def get_round_report_data(conn, round_id):
    """Comprehensive data for the Testing Round Summary printable report.

    Returns dict with:
        rnd            – the testing_rounds row (as dict)
        group_name     – name of the group
        prev_round     – comparison round (baseline or previous retest), or None
        athletes       – list of dicts: id, name, athlete_number, sport,
                         scores {game_key: {field_key: value}},
                         prev_scores {game_key: {field_key: value}},
                         xp_awards [dicts], total_xp int
        games_tested   – ordered list of unique game_keys that have scores
    """
    rnd = conn.execute("SELECT * FROM testing_rounds WHERE id = ?", (round_id,)).fetchone()
    if not rnd:
        return None

    group = conn.execute(
        "SELECT name FROM participant_groups WHERE id = ?", (rnd["group_id"],)
    ).fetchone()
    group_name = group["name"] if group else "Unknown Group"

    prev_round = get_previous_round_for_comparison(conn, round_id)

    # Athletes with at least one score in this round, sorted by name
    athlete_rows = conn.execute(
        "SELECT DISTINCT u.id, u.name, u.athlete_number, u.sport "
        "FROM round_scores rs JOIN users u ON u.id = rs.athlete_id "
        "WHERE rs.round_id = ? ORDER BY u.name",
        (round_id,),
    ).fetchall()

    # Unique game_keys that appear in this round's scores
    game_key_rows = conn.execute(
        "SELECT DISTINCT game_key FROM round_scores WHERE round_id = ? ORDER BY game_key",
        (round_id,),
    ).fetchall()
    games_tested = [r["game_key"] for r in game_key_rows]

    athletes = []
    for ar in athlete_rows:
        aid = ar["id"]
        scores      = get_athlete_round_scores(conn, round_id, aid)
        prev_scores = {} if not prev_round else get_athlete_round_scores(conn, prev_round["id"], aid)
        xp_awards   = get_round_xp_summary(conn, round_id, aid)
        total_xp    = sum(row["xp_awarded"] or 0 for row in xp_awards)
        athletes.append({
            "id":             aid,
            "name":           ar["name"],
            "athlete_number": ar["athlete_number"],
            "sport":          ar["sport"],
            "scores":         scores,
            "prev_scores":    prev_scores,
            "xp_awards":      [dict(x) for x in xp_awards],
            "total_xp":       total_xp,
        })

    return {
        "rnd":         dict(rnd),
        "group_name":  group_name,
        "prev_round":  dict(prev_round) if prev_round else None,
        "athletes":    athletes,
        "games_tested": games_tested,
    }


def get_round_readiness_data(conn, group_ids):
    """Per-group round history and next-available options.

    Returns list of dicts (one per group_id that exists):
        group_id, group_name,
        closed_rounds  – [{id, level, round_type, retest_sequence,
                           opened_at, closed_at, participant_count}]
        open_round     – {id, level, round_type, retest_sequence, opened_at} or None
        next_options   – list from get_available_round_options()
    """
    result = []
    for gid in group_ids:
        group = conn.execute(
            "SELECT name FROM participant_groups WHERE id = ?", (gid,)
        ).fetchone()
        if not group:
            continue

        closed = conn.execute(
            """SELECT tr.id, tr.level, tr.round_type, tr.retest_sequence,
                      tr.opened_at, tr.closed_at,
                      (SELECT COUNT(DISTINCT rs.athlete_id)
                       FROM round_scores rs WHERE rs.round_id = tr.id) AS participant_count
               FROM testing_rounds tr
               WHERE tr.group_id = ? AND tr.status = 'closed'
               ORDER BY tr.id""",
            (gid,),
        ).fetchall()

        open_round = conn.execute(
            "SELECT id, level, round_type, retest_sequence, opened_at "
            "FROM testing_rounds WHERE group_id = ? AND status = 'open'",
            (gid,),
        ).fetchone()

        result.append({
            "group_id":     gid,
            "group_name":   group["name"],
            "closed_rounds": [dict(r) for r in closed],
            "open_round":   dict(open_round) if open_round else None,
            "next_options": get_available_round_options(conn, gid),
        })

    return result


def get_engagement_report_data(conn, athlete_ids):
    """Per-athlete engagement summary for the Engagement & AXP Journey report.

    Returns list of dicts (sorted total_xp desc), each containing:
        id, name, athlete_number, sport,
        total_xp, attendance_count, rounds_count, self_directed_count,
        streak_count, round_axp, last_round_date, last_round_level, last_round_type
    """
    if not athlete_ids:
        return []
    ph = ",".join("?" * len(athlete_ids))
    rows = conn.execute(
        f"""
        SELECT
            u.id, u.name, u.athlete_number, u.sport,
            COALESCE(SUM(xe.amount), 0)                               AS total_xp,
            (SELECT COUNT(*)
             FROM session_attendance sa WHERE sa.participant_id = u.id) AS attendance_count,
            (SELECT COUNT(DISTINCT rs.round_id)
             FROM round_scores rs WHERE rs.athlete_id = u.id)          AS rounds_count,
            (SELECT COUNT(*)
             FROM measurement_sessions ms
             WHERE ms.participant_id = u.id
               AND ms.session_type = 'self_directed')                  AS self_directed_count,
            (SELECT COUNT(*)
             FROM xp_events xe2
             WHERE xe2.participant_id = u.id
               AND xe2.xp_type IN ('streak_3','streak_5'))             AS streak_count,
            (SELECT COALESCE(SUM(rxa.xp_awarded), 0)
             FROM round_xp_awards rxa WHERE rxa.athlete_id = u.id)    AS round_axp,
            (SELECT MAX(tr.closed_at)
             FROM testing_rounds tr
             JOIN round_scores rs3 ON rs3.round_id = tr.id
             WHERE rs3.athlete_id = u.id AND tr.status = 'closed')    AS last_round_date,
            (SELECT tr2.level
             FROM testing_rounds tr2
             JOIN round_scores rs4 ON rs4.round_id = tr2.id
             WHERE rs4.athlete_id = u.id AND tr2.status = 'closed'
             ORDER BY tr2.closed_at DESC LIMIT 1)                      AS last_round_level,
            (SELECT tr3.round_type
             FROM testing_rounds tr3
             JOIN round_scores rs5 ON rs5.round_id = tr3.id
             WHERE rs5.athlete_id = u.id AND tr3.status = 'closed'
             ORDER BY tr3.closed_at DESC LIMIT 1)                      AS last_round_type
        FROM users u
        LEFT JOIN xp_events xe ON xe.participant_id = u.id
        WHERE u.id IN ({ph})
        GROUP BY u.id
        ORDER BY total_xp DESC
        """,
        athlete_ids,
    ).fetchall()
    return [dict(r) for r in rows]


def get_cohort_improvement_data(conn, group_ids):
    """Aggregate testing-round improvement data for the Cohort Improvement Report.

    Returns a dict keyed by level (int), each value:
        {
          "baselines": [round_dict, ...],   # closed baseline rounds (with participant_count)
          "retests":   [round_dict, ...],   # closed retest rounds (with game_stats list)
        }

    game_stats per retest round:
        {"game_key", "game_name", "avg_improvement", "athlete_count", "improved_count"}
    """
    if not group_ids:
        return {}
    ph = ",".join("?" * len(group_ids))
    rounds = conn.execute(
        f"SELECT tr.*, pg.name AS group_name, "
        f"(SELECT COUNT(DISTINCT rs.athlete_id) FROM round_scores rs WHERE rs.round_id = tr.id) AS participant_count "
        f"FROM testing_rounds tr "
        f"JOIN participant_groups pg ON pg.id = tr.group_id "
        f"WHERE tr.group_id IN ({ph}) AND tr.status = 'closed' "
        f"ORDER BY tr.level, tr.round_type, tr.id",
        group_ids,
    ).fetchall()

    by_level = {}
    for rnd in rounds:
        rnd = dict(rnd)
        lvl = rnd["level"]
        by_level.setdefault(lvl, {"baselines": [], "retests": []})
        bucket = "retests" if rnd["round_type"] == "retest" else "baselines"
        by_level[lvl][bucket].append(rnd)

    # For each retest round, pull per-game improvement stats from round_xp_awards
    for lvl, data in by_level.items():
        for rnd in data["retests"]:
            rows = conn.execute(
                "SELECT game_key, "
                "AVG(improvement_pct) AS avg_improvement, "
                "COUNT(DISTINCT athlete_id) AS athlete_count, "
                "SUM(CASE WHEN improvement_pct > 0 THEN 1 ELSE 0 END) AS improved_count "
                "FROM round_xp_awards "
                "WHERE round_id = ? AND award_type = 'improvement' "
                "AND improvement_pct IS NOT NULL AND game_key IS NOT NULL "
                "GROUP BY game_key ORDER BY avg_improvement DESC",
                (rnd["id"],),
            ).fetchall()
            rnd["game_stats"] = [dict(r) for r in rows]

    return by_level


def get_athlete_testing_history(conn, athlete_id, group_id=None):
    """Return all closed rounds an athlete has scores in, with total XP earned per round."""
    q = (
        "SELECT tr.id, tr.level, tr.round_type, tr.retest_sequence, tr.closed_at, "
        "tr.group_id, COALESCE(SUM(rxa.xp_awarded), 0) AS total_xp "
        "FROM testing_rounds tr "
        "JOIN round_scores rs ON rs.round_id = tr.id AND rs.athlete_id = ? "
        "LEFT JOIN round_xp_awards rxa ON rxa.round_id = tr.id AND rxa.athlete_id = ? "
        "WHERE tr.status = 'closed'"
    )
    params = [athlete_id, athlete_id]
    if group_id:
        q += " AND tr.group_id = ?"
        params.append(group_id)
    q += " GROUP BY tr.id ORDER BY tr.id"
    return conn.execute(q, params).fetchall()


def _check_level_thresholds(conn, participant_id, game_key, results_for_game, session_id):
    """Check if this session's results earn any new levels across all scoring areas
    for this game_key. Awards them and returns list of (field_key, level) tuples earned.

    Handles two cases:
    - Standard games (field_key != ''): one threshold per level, one achievement per level.
    - Multi-field games (Balance Ball): separate threshold + achievement per field_key.
    - Pooled games (Diamond Gates/Dribble): any score_field meeting the threshold earns the level.
    """
    from constants import SCORING_AREAS, XP_GAME_CONFIG, threshold_field_key
    XP_GAME_CONFIG_local, LEVEL_XP_AWARDS = _import_xp_constants()[:2]

    new_levels = []

    # Find all scoring areas for this game_key
    areas_for_game = [a for a in SCORING_AREAS if a["game_key"] == game_key]
    if not areas_for_game:
        return new_levels

    for area in areas_for_game:
        area_field_key = area["field_key"]  # None = pooled, str = specific field
        stored_field_key = threshold_field_key(area)  # key used in thresholds table
        # field_key stored in level_achievements for this area
        achievement_field_key = area_field_key or ""

        current_level = get_athlete_level(conn, participant_id, game_key, achievement_field_key)

        for target_level in range(1, 6):
            if target_level <= current_level:
                continue
            threshold = get_game_threshold(conn, game_key, target_level, stored_field_key)
            if not threshold:
                continue
            threshold_val = threshold["threshold_value"]
            lower_is_better = bool(threshold["lower_is_better"])

            # Determine which fields to check
            if area_field_key is None:
                # Pooled: check all score_fields from XP_GAME_CONFIG
                cfg = XP_GAME_CONFIG_local.get(game_key, {})
                fields_to_check = cfg.get("score_fields", [])
            else:
                fields_to_check = [area_field_key]

            earned = False
            for fk in fields_to_check:
                score = results_for_game.get(fk)
                if score is None:
                    continue
                try:
                    score = float(score)
                except (TypeError, ValueError):
                    continue
                if (score <= threshold_val) if lower_is_better else (score >= threshold_val):
                    earned = True
                    break

            if earned:
                awarded = award_level(conn, participant_id, game_key, target_level,
                                      field_key=achievement_field_key, session_id=session_id)
                if awarded:
                    new_levels.append((achievement_field_key, target_level))
                    xp_amount = LEVEL_XP_AWARDS.get(target_level, 0)
                    if xp_amount:
                        notes_area = area["display_name"]
                        award_xp(conn, participant_id, "level_achievement", xp_amount,
                                 game_key=game_key, session_id=session_id,
                                 notes=f"Earned Level {target_level} in {notes_area}")
    return new_levels


# ── Breadth / Milestone helpers ───────────────────────────────────────────────

def _has_played_game_before(conn, participant_id, game_key, current_session_id):
    """True if there's an earlier session (not this one) with a result for this game."""
    row = conn.execute(
        "SELECT mr.id FROM measurement_results mr "
        "JOIN measurement_sessions ms ON ms.id = mr.session_id "
        "WHERE ms.participant_id = ? AND mr.game_key = ? AND ms.id != ? "
        "ORDER BY ms.id ASC LIMIT 1",
        (participant_id, game_key, current_session_id),
    ).fetchone()
    return row is not None


def _check_all_8_in_session(conn, session_id):
    """Return list of core game keys that have at least one result in this session."""
    XP_GAME_CONFIG, LEVEL_XP_AWARDS, XP_RANK_TIERS, XP_PARTICIPATION, CORE_AAP_GAMES = _import_xp_constants()
    rows = conn.execute(
        "SELECT DISTINCT game_key FROM measurement_results WHERE session_id = ?",
        (session_id,),
    ).fetchall()
    played = {r["game_key"] for r in rows}
    return [g for g in CORE_AAP_GAMES if g in played]


def _has_awarded_xp_type_for_session(conn, participant_id, xp_type, session_id, game_key=None):
    """True if this xp_type has already been awarded for this session (prevents double-up).
    Pass game_key to restrict the check to a specific game."""
    if game_key is not None:
        row = conn.execute(
            "SELECT id FROM xp_events WHERE participant_id = ? AND xp_type = ? "
            "AND game_key = ? AND session_id = ?",
            (participant_id, xp_type, game_key, session_id),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id FROM xp_events WHERE participant_id = ? AND xp_type = ? AND session_id = ?",
            (participant_id, xp_type, session_id),
        ).fetchone()
    return row is not None


def _has_awarded_xp_type(conn, participant_id, xp_type):
    """True if this xp_type has been awarded at any point (for one-time bonuses)."""
    row = conn.execute(
        "SELECT id FROM xp_events WHERE participant_id = ? AND xp_type = ?",
        (participant_id, xp_type),
    ).fetchone()
    return row is not None


# ── Main entry point ──────────────────────────────────────────────────────────

def process_session_xp(conn, session_id, participant_id, is_formal=True):
    """Calculate and award all XP for a completed measurement session.

    Call this after saving all results for a session. Fully idempotent —
    safe to call multiple times for the same session (duplicate guards in place).
    is_formal=True  → formal test session (counts for levels, higher XP rates)
    is_formal=False → self-directed session (XP only, never triggers levels)

    Returns a summary dict with total_xp_awarded and breakdown list.
    """
    XP_GAME_CONFIG, LEVEL_XP_AWARDS, XP_RANK_TIERS, XP_PARTICIPATION, CORE_AAP_GAMES = _import_xp_constants()

    awarded = []  # list of (xp_type, amount, game_key, notes) tuples for the summary

    # Load all results for this session into a nested dict: {game_key: {field_key: value}}
    rows = conn.execute(
        "SELECT game_key, field_key, value FROM measurement_results WHERE session_id = ?",
        (session_id,),
    ).fetchall()
    session_results = {}
    for r in rows:
        session_results.setdefault(r["game_key"], {})[r["field_key"]] = r["value"]

    games_played = [gk for gk in session_results if gk in CORE_AAP_GAMES]

    if not games_played:
        return {"total_xp_awarded": 0, "breakdown": []}

    participation_type = "formal_game" if is_formal else "self_directed_game"
    pb_type = "pb_formal" if is_formal else "pb_self_directed"
    ingame_type = "ingame_formal" if is_formal else "ingame_self"

    # ── Welcome bonus (one-time ever) ────────────────────────────────────────
    if not _has_awarded_xp_type(conn, participant_id, "welcome_bonus"):
        amt = XP_PARTICIPATION["welcome_bonus"]
        award_xp(conn, participant_id, "welcome_bonus", amt,
                 session_id=session_id, notes="First session welcome bonus")
        awarded.append(("welcome_bonus", amt, None, "Welcome bonus"))

    for game_key in games_played:
        game_results = session_results[game_key]
        cfg = XP_GAME_CONFIG.get(game_key)
        if not cfg:
            continue

        # ── First-time-playing bonus (per game, one-time) ─────────────────
        if not _has_played_game_before(conn, participant_id, game_key, session_id):
            if not conn.execute(
                "SELECT id FROM xp_events WHERE participant_id = ? AND xp_type = 'breadth_first_game' AND game_key = ?",
                (participant_id, game_key),
            ).fetchone():
                amt = XP_PARTICIPATION["first_game"]
                award_xp(conn, participant_id, "breadth_first_game", amt,
                         game_key=game_key, session_id=session_id,
                         notes=f"First time playing {game_key}")
                awarded.append(("breadth_first_game", amt, game_key, "First time"))

        # ── Participation XP (per game per session) ───────────────────────
        if not _has_awarded_xp_type_for_session(conn, participant_id, participation_type, session_id, game_key=game_key):
            amt = XP_PARTICIPATION[participation_type]
            award_xp(conn, participant_id, participation_type, amt,
                     game_key=game_key, session_id=session_id,
                     notes=f"Participation — {game_key}")
            awarded.append((participation_type, amt, game_key, "Participation"))

        # ── In-game XP from score ────────────────────────────────────────
        if not _has_awarded_xp_type_for_session(conn, participant_id, ingame_type, session_id, game_key=game_key):
            ingame_xp = 0
            if cfg["xp_type"] == "count":
                multiplier = cfg["multiplier"]
                for field_key in cfg["score_fields"]:
                    raw = game_results.get(field_key)
                    if raw is not None:
                        try:
                            ingame_xp += int(float(raw)) * multiplier
                        except (TypeError, ValueError):
                            pass
            elif cfg["xp_type"] == "improvement":
                # Handled below under PB section for improvement games
                pass

            if ingame_xp > 0:
                award_xp(conn, participant_id, ingame_type, ingame_xp,
                         game_key=game_key, session_id=session_id,
                         notes=f"In-game score — {game_key}")
                awarded.append((ingame_type, ingame_xp, game_key, "In-game score"))

        # ── PB tracking and PB XP ────────────────────────────────────────
        primary_field = cfg.get("primary_field")
        if primary_field and primary_field in game_results:
            raw_score = game_results[primary_field]
            try:
                score = float(raw_score)
            except (TypeError, ValueError):
                score = None

            if score is not None:
                is_pb, improvement = update_personal_best(
                    conn, participant_id, game_key, primary_field,
                    score, session_id=session_id, is_formal=is_formal,
                )
                if is_pb and not _has_awarded_xp_type_for_session(
                    conn, participant_id, pb_type, session_id, game_key=game_key
                ):
                    pb_xp = 0
                    if cfg["xp_type"] == "improvement" and improvement is not None:
                        # 5 XP per unit_size improvement
                        unit_size = cfg.get("unit_size", 0.1)
                        xp_per_unit = cfg.get("xp_per_unit", 5)
                        units = improvement / unit_size
                        pb_xp = max(0, int(units) * xp_per_unit)
                    else:
                        pb_xp = XP_PARTICIPATION[pb_type]

                    if pb_xp > 0:
                        award_xp(conn, participant_id, pb_type, pb_xp,
                                 game_key=game_key, session_id=session_id,
                                 notes=f"Personal best — {game_key} ({score})")
                        awarded.append((pb_type, pb_xp, game_key, f"PB {score}"))

    # ── All 8 core games in one session bonus ─────────────────────────────
    core_in_session = _check_all_8_in_session(conn, session_id)
    if len(core_in_session) >= 8:
        if not _has_awarded_xp_type_for_session(conn, participant_id, "all_8_session", session_id):
            amt = XP_PARTICIPATION["all_8_session"]
            award_xp(conn, participant_id, "all_8_session", amt,
                     session_id=session_id, notes="All 8 core games in one session")
            awarded.append(("all_8_session", amt, None, "All 8 games bonus"))

    total = sum(a[1] for a in awarded)
    return {
        "total_xp_awarded": total,
        "breakdown": [
            {"xp_type": a[0], "amount": a[1], "game_key": a[2], "notes": a[3]}
            for a in awarded
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# ATTENDANCE & SELF-DIRECTED SESSION FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def create_session_event(conn, group_id, date, created_by, notes=None):
    """Create a new session event (training day). Returns event_id.
    is_open defaults to 0 — practitioner explicitly opens self-test via open_session_event()."""
    eid = conn.execute(
        "INSERT INTO session_events (group_id, date, notes, created_by, created_at, is_open) "
        "VALUES (?, ?, ?, ?, ?, 0)",
        (group_id or None, date, notes or None, created_by, now()),
    ).lastrowid
    conn.commit()
    return eid


def open_session_event(conn, event_id):
    """Open self-test window for a session event. Records opened_at timestamp in notes is avoided —
    we reuse created_at as the start reference but stamp is_open and opened_at separately."""
    conn.execute(
        "UPDATE session_events SET is_open = 1, opened_at = ? WHERE id = ?",
        (now(), event_id),
    )
    conn.commit()


def close_session_event(conn, event_id):
    """Close self-test window for a session event."""
    conn.execute("UPDATE session_events SET is_open = 0 WHERE id = ?", (event_id,))
    conn.commit()


def mark_onboarding_seen(conn, user_id):
    """Flag that this practitioner has dismissed the onboarding callout."""
    conn.execute("UPDATE users SET onboarding_seen = 1 WHERE id = ?", (user_id,))
    conn.commit()


def get_session_event(conn, event_id):
    """Return a session event dict with group name joined in."""
    return conn.execute(
        "SELECT se.*, pg.name AS group_name, u.name AS created_by_name "
        "FROM session_events se "
        "LEFT JOIN participant_groups pg ON pg.id = se.group_id "
        "LEFT JOIN users u ON u.id = se.created_by "
        "WHERE se.id = ?",
        (event_id,),
    ).fetchone()


def list_session_events(conn, group_id=None, limit=30):
    """List recent session events, optionally filtered by group."""
    if group_id:
        return conn.execute(
            "SELECT se.*, pg.name AS group_name, "
            "(SELECT COUNT(*) FROM session_attendance sa WHERE sa.event_id = se.id) AS attendee_count "
            "FROM session_events se "
            "LEFT JOIN participant_groups pg ON pg.id = se.group_id "
            "WHERE se.group_id = ? ORDER BY se.date DESC, se.id DESC LIMIT ?",
            (group_id, limit),
        ).fetchall()
    return conn.execute(
        "SELECT se.*, pg.name AS group_name, "
        "(SELECT COUNT(*) FROM session_attendance sa WHERE sa.event_id = se.id) AS attendee_count "
        "FROM session_events se "
        "LEFT JOIN participant_groups pg ON pg.id = se.group_id "
        "ORDER BY se.date DESC, se.id DESC LIMIT ?",
        (limit,),
    ).fetchall()


def list_session_events_for_coach(conn, coach_id, limit=30):
    """Session events for groups assigned to a specific coach."""
    group_ids = get_coach_group_ids(conn, coach_id)
    if not group_ids:
        return []
    placeholders = ",".join("?" * len(group_ids))
    return conn.execute(
        f"SELECT se.*, pg.name AS group_name, "
        f"(SELECT COUNT(*) FROM session_attendance sa WHERE sa.event_id = se.id) AS attendee_count "
        f"FROM session_events se "
        f"LEFT JOIN participant_groups pg ON pg.id = se.group_id "
        f"WHERE se.group_id IN ({placeholders}) "
        f"ORDER BY se.date DESC, se.id DESC LIMIT ?",
        group_ids + [limit],
    ).fetchall()


def mark_attendance(conn, event_id, participant_ids, marked_by):
    """Replace attendance for an event with the given list of participant IDs.
    Idempotent — safe to call multiple times (replaces previous marks)."""
    conn.execute("DELETE FROM session_attendance WHERE event_id = ?", (event_id,))
    for pid in participant_ids:
        conn.execute(
            "INSERT OR IGNORE INTO session_attendance (event_id, participant_id, marked_by, created_at) "
            "VALUES (?, ?, ?, ?)",
            (event_id, pid, marked_by, now()),
        )
    conn.commit()


def get_attendance_for_event(conn, event_id):
    """Return list of participant dicts who attended a session event."""
    return conn.execute(
        "SELECT u.*, sa.created_at AS marked_at "
        "FROM session_attendance sa "
        "JOIN users u ON u.id = sa.participant_id "
        "WHERE sa.event_id = ? ORDER BY u.name",
        (event_id,),
    ).fetchall()


def get_attended_event_ids(conn, participant_id):
    """Return set of event_ids the athlete has been marked present for."""
    rows = conn.execute(
        "SELECT event_id FROM session_attendance WHERE participant_id = ?",
        (participant_id,),
    ).fetchall()
    return {r["event_id"] for r in rows}


def count_attendance(conn, participant_id):
    """Total number of sessions the athlete has been marked present for."""
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM session_attendance WHERE participant_id = ?",
        (participant_id,),
    ).fetchone()
    return row["c"]


def get_pending_self_directed_events(conn, participant_id):
    """Return open session events the athlete attended but hasn't yet scored self-directed results for.
    Only returns events where is_open = 1 (practitioner has opened the self-test window)."""
    return conn.execute(
        "SELECT se.*, pg.name AS group_name "
        "FROM session_attendance sa "
        "JOIN session_events se ON se.id = sa.event_id "
        "LEFT JOIN participant_groups pg ON pg.id = se.group_id "
        "WHERE sa.participant_id = ? "
        "AND se.is_open = 1 "
        "AND NOT EXISTS ("
        "  SELECT 1 FROM measurement_sessions ms "
        "  WHERE ms.participant_id = ? AND ms.attendance_event_id = se.id "
        "  AND ms.session_type = 'self_directed'"
        ") "
        "ORDER BY se.date DESC",
        (participant_id, participant_id),
    ).fetchall()


def get_self_directed_sessions(conn, participant_id):
    """Return all self-directed measurement sessions for an athlete, most recent first."""
    sessions = conn.execute(
        "SELECT ms.*, se.date AS event_date, pg.name AS group_name "
        "FROM measurement_sessions ms "
        "LEFT JOIN session_events se ON se.id = ms.attendance_event_id "
        "LEFT JOIN participant_groups pg ON pg.id = se.group_id "
        "WHERE ms.participant_id = ? AND ms.session_type = 'self_directed' "
        "ORDER BY ms.date DESC, ms.id DESC",
        (participant_id,),
    ).fetchall()
    out = []
    for s in sessions:
        rows = conn.execute(
            "SELECT game_key, field_key, value FROM measurement_results WHERE session_id = ?",
            (s["id"],),
        ).fetchall()
        d = dict(s)
        d["results"] = {(r["game_key"], r["field_key"]): r["value"] for r in rows}
        out.append(d)
    return out


def create_self_directed_session(conn, participant_id, event_id, results, logged_by=None):
    """Create a self-directed measurement session linked to an attendance event.
    results: iterable of (game_key, field_key, value) tuples.
    Returns session_id."""
    # Get the date from the event
    event = conn.execute("SELECT date, group_id FROM session_events WHERE id = ?", (event_id,)).fetchone()
    if not event:
        raise ValueError(f"Session event {event_id} not found")
    date = event["date"]
    group_id = event["group_id"]

    session_id = conn.execute(
        "INSERT INTO measurement_sessions "
        "(participant_id, group_id, date, logged_by, created_at, session_type, attendance_event_id) "
        "VALUES (?, ?, ?, ?, ?, 'self_directed', ?)",
        (participant_id, group_id, date, logged_by or participant_id, now(), event_id),
    ).lastrowid
    for game_key, field_key, value in results:
        conn.execute(
            "INSERT INTO measurement_results (session_id, game_key, field_key, value) VALUES (?, ?, ?, ?)",
            (session_id, game_key, field_key, value),
        )
    conn.commit()
    return session_id


def check_attendance_milestones(conn, participant_id, session_id):
    """Check and award XP for attendance-based session milestones (10th/25th/50th session).
    Called after marking attendance. Returns list of (xp_type, amount) tuples awarded."""
    total = count_attendance(conn, participant_id)
    awarded = []
    milestones = [(10, "milestone_10", 150), (25, "milestone_25", 300), (50, "milestone_50", 600)]
    for threshold, xp_type, amount in milestones:
        if total >= threshold and not _has_awarded_xp_type(conn, participant_id, xp_type):
            award_xp(conn, participant_id, xp_type, amount,
                     session_id=session_id,
                     notes=f"{threshold}th session milestone")
            awarded.append((xp_type, amount))
    return awarded


def check_attendance_streak(conn, participant_id):
    """Check and award streak XP after an attendance mark.
    A streak is the count of *consecutive* session_events this athlete attended,
    counting backwards from the most recent.  Streaks reset when they miss a
    session_event that their group was listed for (or any event if ungrouped).

    Streak milestones: 3 consecutive → 30 XP (streak_3), 5 → 75 XP (streak_5).
    Awards are per-streak-count, not per-session, so each tier is awarded once per
    streak run.  Returns list of (xp_type, amount) awarded this call.

    Implementation note: because we only record who *attended* (not who was absent),
    we determine a missed session as any session_event in the relevant group date range
    where the athlete does NOT appear in session_attendance.  To keep this lightweight
    we look only at the most recent 10 events in the athlete's group(s) and count
    the trailing streak from the newest event backwards.
    """
    # Get the athlete's current group (most recent assignment)
    group_row = conn.execute(
        "SELECT group_id FROM participant_group_memberships WHERE participant_id = ? "
        "ORDER BY id DESC LIMIT 1",
        (participant_id,),
    ).fetchone()
    group_id = group_row["group_id"] if group_row else None

    # Get recent session events for this group (or all events if ungrouped)
    if group_id:
        events = conn.execute(
            "SELECT id FROM session_events WHERE group_id = ? OR group_id IS NULL "
            "ORDER BY date DESC, id DESC LIMIT 10",
            (group_id,),
        ).fetchall()
    else:
        events = conn.execute(
            "SELECT id FROM session_events ORDER BY date DESC, id DESC LIMIT 10"
        ).fetchall()

    if not events:
        return []

    # Which of those events did the athlete attend?
    attended_ids = set(
        r["event_id"]
        for r in conn.execute(
            "SELECT event_id FROM session_attendance WHERE participant_id = ?",
            (participant_id,),
        ).fetchall()
    )

    # Count consecutive from most recent, stopping at first miss
    streak = 0
    for e in events:
        if e["id"] in attended_ids:
            streak += 1
        else:
            break  # gap found — streak ends here

    awarded = []
    XP_PARTICIPATION = _import_xp_constants()[3]
    # Award streak_3 once per streak run (idempotent via count check)
    # We use the most recently attended event_id as the anchor session_id
    latest_attended = next((e["id"] for e in events if e["id"] in attended_ids), None)
    if streak >= 3:
        already = conn.execute(
            "SELECT COUNT(*) AS n FROM xp_events WHERE participant_id = ? AND xp_type = 'streak_3' "
            "AND session_id = ?",
            (participant_id, latest_attended),
        ).fetchone()["n"]
        if not already:
            amt = XP_PARTICIPATION.get("streak_3", 30)
            award_xp(conn, participant_id, "streak_3", amt,
                     session_id=latest_attended,
                     notes=f"3-session streak")
            awarded.append(("streak_3", amt))
    if streak >= 5:
        already = conn.execute(
            "SELECT COUNT(*) AS n FROM xp_events WHERE participant_id = ? AND xp_type = 'streak_5' "
            "AND session_id = ?",
            (participant_id, latest_attended),
        ).fetchone()["n"]
        if not already:
            amt = XP_PARTICIPATION.get("streak_5", 75)
            award_xp(conn, participant_id, "streak_5", amt,
                     session_id=latest_attended,
                     notes=f"5-session streak")
            awarded.append(("streak_5", amt))
    return awarded


def retroactive_welcome_bonus(conn):
    """Award welcome_bonus XP (100 XP) to every participant who doesn't already
    have it. Idempotent — safe to run repeatedly. Called automatically from
    retroactive_xp_pass and from init_db on each startup.
    Returns count of athletes newly awarded."""
    from constants import XP_PARTICIPATION
    amount = XP_PARTICIPATION.get("welcome_bonus", 100)
    participants = conn.execute(
        "SELECT id FROM users WHERE role = 'participant' AND active = 1"
    ).fetchall()
    awarded = 0
    for p in participants:
        if not _has_awarded_xp_type(conn, p["id"], "welcome_bonus"):
            award_xp(conn, p["id"], "welcome_bonus", amount,
                     notes="Welcome to Just a Game!")
            awarded += 1
    return awarded


def retroactive_xp_pass(conn):
    """One-time pass: award XP for all existing formal measurement sessions,
    and ensure every participant has their welcome bonus.
    Run once after deploying the XP engine. Idempotent — skips sessions that
    already have XP events. Returns count of sessions processed."""
    # Ensure all athletes have welcome bonus
    retroactive_welcome_bonus(conn)

    sessions = conn.execute(
        "SELECT id, participant_id FROM measurement_sessions ORDER BY date ASC, id ASC"
    ).fetchall()
    processed = 0
    for s in sessions:
        # Skip if this session already has any XP events
        existing = conn.execute(
            "SELECT id FROM xp_events WHERE session_id = ? LIMIT 1", (s["id"],)
        ).fetchone()
        if existing:
            continue
        process_session_xp(conn, s["id"], s["participant_id"], is_formal=True)
        processed += 1
    return processed


def retroactive_level_pass(conn):
    """Re-check level thresholds across ALL sessions regardless of whether they
    already have XP events.  Must be run whenever thresholds are first set (or
    changed) because the main retroactive_xp_pass skips already-processed sessions.

    Fully idempotent: award_level uses a UNIQUE constraint so levels cannot be
    double-awarded. The accompanying level_achievement XP is guarded the same way.
    Returns (levels_awarded, xp_awarded) counts."""
    sessions = conn.execute(
        "SELECT id, participant_id FROM measurement_sessions ORDER BY date ASC, id ASC"
    ).fetchall()

    levels_awarded = 0
    xp_awarded = 0

    for s in sessions:
        session_id = s["id"]
        participant_id = s["participant_id"]

        # Load all results for this session
        rows = conn.execute(
            "SELECT game_key, field_key, value FROM measurement_results WHERE session_id = ?",
            (session_id,),
        ).fetchall()
        session_results = {}
        for r in rows:
            session_results.setdefault(r["game_key"], {})[r["field_key"]] = r["value"]

        for game_key, game_results in session_results.items():
            new_levels = _check_level_thresholds(
                conn, participant_id, game_key, game_results, session_id
            )
            for (fk, lvl) in new_levels:
                levels_awarded += 1
                from constants import LEVEL_XP_AWARDS
                xp_awarded += LEVEL_XP_AWARDS.get(lvl, 0)

    return levels_awarded, xp_awarded


def cleanup_demo_data():
    """One-time cleanup: removes demo participants, their sessions/results,
    and the Demo Group from the live database.
    Idempotent — safe to run on every startup, does nothing once already clean."""
    print("cleanup_demo_data: starting", flush=True)
    conn = get_conn()
    try:
        demo_emails = [
            "alex.demo@example.com",
            "jess.demo@example.com",
            "sam.demo@example.com",
        ]
        # Find demo participant IDs
        demo_ids = []
        for email in demo_emails:
            row = conn.execute(
                "SELECT id FROM users WHERE email = ? AND role = 'participant'", (email,)
            ).fetchone()
            if row:
                demo_ids.append(row["id"])

        if not demo_ids:
            print("cleanup_demo_data: no demo participants found, nothing to do", flush=True)
        else:
            # Delete measurement results and sessions for demo participants
            for pid in demo_ids:
                session_ids = [
                    r["id"] for r in conn.execute(
                        "SELECT id FROM measurement_sessions WHERE participant_id = ?", (pid,)
                    ).fetchall()
                ]
                for sid in session_ids:
                    conn.execute("DELETE FROM measurement_results WHERE session_id = ?", (sid,))
                conn.execute("DELETE FROM measurement_sessions WHERE participant_id = ?", (pid,))
            # Delete the demo participant accounts
            conn.execute(
                "DELETE FROM users WHERE email IN ({})".format(",".join("?" * len(demo_emails))),
                demo_emails,
            )
            conn.commit()
            print(f"cleanup_demo_data: removed {len(demo_ids)} demo participants", flush=True)

        # Delete the Demo Group (best-effort — skip on any error)
        try:
            group = conn.execute(
                "SELECT id FROM participant_groups WHERE lower(name) = 'demo group'"
            ).fetchone()
            if group:
                gid = group["id"]
                # Remove coach-group assignments first (FK constraint)
                conn.execute("DELETE FROM coach_groups WHERE group_id = ?", (gid,))
                # Unlink any participants still in this group
                conn.execute("UPDATE users SET group_id = NULL WHERE group_id = ?", (gid,))
                conn.execute("DELETE FROM participant_groups WHERE id = ?", (gid,))
                conn.commit()
                print("cleanup_demo_data: removed Demo Group", flush=True)
            else:
                print("cleanup_demo_data: Demo Group not found, nothing to do", flush=True)
        except Exception as e:
            print(f"cleanup_demo_data: could not remove Demo Group ({e}), skipping", flush=True)

        print("cleanup_demo_data: complete", flush=True)
    finally:
        conn.close()


# ── Measurement Windows ───────────────────────────────────────────────────────

# ── Threshold helpers (retained — used by score distribution + SC gap report) ─

def get_all_thresholds(conn):
    """Return all rows from game_thresholds, or [] if the table doesn't exist."""
    try:
        return conn.execute(
            "SELECT game_key, field_key, level, threshold_value, lower_is_better "
            "FROM game_thresholds ORDER BY game_key, level, field_key"
        ).fetchall()
    except Exception:
        return []


def get_game_threshold(conn, game_key, level, field_key=None):
    """Return threshold row for a specific game/level/field, or None."""
    try:
        if field_key:
            return conn.execute(
                "SELECT * FROM game_thresholds WHERE game_key=? AND level=? AND field_key=?",
                (game_key, level, field_key)
            ).fetchone()
        return conn.execute(
            "SELECT * FROM game_thresholds WHERE game_key=? AND level=?",
            (game_key, level)
        ).fetchone()
    except Exception:
        return None


def set_game_threshold(conn, game_key, level, field_key, threshold_value,
                       lower_is_better=False, set_by=None):
    """Upsert a threshold value."""
    now_ts = now()
    conn.execute(
        "INSERT INTO game_thresholds (game_key, field_key, level, threshold_value, "
        "lower_is_better, set_by, set_at) VALUES (?,?,?,?,?,?,?) "
        "ON CONFLICT(game_key, field_key, level) DO UPDATE SET "
        "threshold_value=excluded.threshold_value, "
        "lower_is_better=excluded.lower_is_better, set_at=excluded.set_at",
        (game_key, field_key, level, threshold_value, int(lower_is_better), set_by, now_ts)
    )
    conn.commit()


def delete_game_threshold(conn, game_key, level, field_key=None):
    """Delete one or all thresholds for a game/level."""
    if field_key:
        conn.execute(
            "DELETE FROM game_thresholds WHERE game_key=? AND level=? AND field_key=?",
            (game_key, level, field_key)
        )
    else:
        conn.execute(
            "DELETE FROM game_thresholds WHERE game_key=? AND level=?",
            (game_key, level)
        )
    conn.commit()


def open_measurement_window(conn, group_id, opened_by, session_label=None, session_month=None):
    # DEPRECATED — use open_testing_round instead. Retained for migration safety.
    """Open a new measurement window for a group. Returns the new window id."""
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "INSERT INTO measurement_windows (group_id, opened_by, opened_at, status, session_label, session_month) "
        "VALUES (?, ?, ?, 'open', ?, ?)",
        (group_id, opened_by, now, session_label, session_month),
    )
    conn.commit()
    return cur.lastrowid


def get_measurement_window(conn, window_id):
    """Return a single window row or None."""
    return conn.execute(
        "SELECT mw.*, pg.name AS group_name, u.name AS opened_by_name "
        "FROM measurement_windows mw "
        "JOIN participant_groups pg ON pg.id = mw.group_id "
        "JOIN users u ON u.id = mw.opened_by "
        "WHERE mw.id = ?",
        (window_id,),
    ).fetchone()


def get_active_window_for_group(conn, group_id):
    """Return the open window for a group, or None."""
    return conn.execute(
        "SELECT * FROM measurement_windows WHERE group_id = ? AND status = 'open' ORDER BY opened_at DESC LIMIT 1",
        (group_id,),
    ).fetchone()


def get_active_window_for_participant(conn, participant_id):
    """Return the open window for the participant's group, or None."""
    row = conn.execute(
        "SELECT group_id FROM users WHERE id = ?", (participant_id,)
    ).fetchone()
    if not row or not row["group_id"]:
        return None
    return get_active_window_for_group(conn, row["group_id"])


def get_window_submissions(conn, window_id):
    """Return all submissions for a window, with participant info."""
    return conn.execute(
        "SELECT ws.*, u.name AS participant_name, u.athlete_number "
        "FROM window_submissions ws "
        "JOIN users u ON u.id = ws.participant_id "
        "WHERE ws.window_id = ? "
        "ORDER BY ws.submitted_at",
        (window_id,),
    ).fetchall()


def athlete_has_submitted(conn, window_id, participant_id):
    """True if this athlete already has a submission for the window."""
    return conn.execute(
        "SELECT id FROM window_submissions WHERE window_id = ? AND participant_id = ?",
        (window_id, participant_id),
    ).fetchone() is not None


def create_window_submission(conn, window_id, participant_id, session_id):
    """Record an athlete's submission. Raises on duplicate (UNIQUE constraint)."""
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO window_submissions (window_id, participant_id, session_id, submitted_at, committed) "
        "VALUES (?, ?, ?, ?, 0)",
        (window_id, participant_id, session_id, now),
    )
    conn.commit()


def close_measurement_window(conn, window_id):
    """Close the window. Returns list of (session_id, participant_id) for uncommitted
    submissions so the caller can run XP processing on each."""
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    # Fetch uncommitted submissions before marking them committed
    rows = conn.execute(
        "SELECT session_id, participant_id FROM window_submissions "
        "WHERE window_id = ? AND committed = 0 AND session_id IS NOT NULL",
        (window_id,),
    ).fetchall()
    # Mark all submissions as committed and close the window
    conn.execute(
        "UPDATE window_submissions SET committed = 1 WHERE window_id = ? AND committed = 0",
        (window_id,),
    )
    conn.execute(
        "UPDATE measurement_windows SET status = 'closed', closed_at = ? WHERE id = ?",
        (now, window_id),
    )
    conn.commit()
    return [(r["session_id"], r["participant_id"]) for r in rows]


def reopen_measurement_window(conn, window_id):
    """Reopen a closed window so absentees can submit. Already-committed
    submissions are not touched."""
    conn.execute(
        "UPDATE measurement_windows SET status = 'open', closed_at = NULL WHERE id = ?",
        (window_id,),
    )
    conn.commit()


def get_recent_windows_for_group(conn, group_id, limit=5):
    """Return recent windows for a group (open first, then most recently closed)."""
    return conn.execute(
        "SELECT mw.*, u.name AS opened_by_name, "
        "(SELECT COUNT(*) FROM window_submissions ws WHERE ws.window_id = mw.id) AS submission_count "
        "FROM measurement_windows mw "
        "JOIN users u ON u.id = mw.opened_by "
        "WHERE mw.group_id = ? "
        "ORDER BY CASE WHEN mw.status = 'open' THEN 0 ELSE 1 END, mw.opened_at DESC "
        "LIMIT ?",
        (group_id, limit),
    ).fetchall()


def maybe_reset_coach_password():
    """Recovery hatch for a forgotten coach password on a host (like
    Render's free tier) with no shell access. If the RESET_COACH_PASSWORD
    environment variable is set at startup, update the matching coach
    account's password to that value and clear their existing sessions.
    Matches on the COACH_EMAIL env var if set, otherwise the first coach
    account found (there is normally only one). Touches nothing else --
    no activities, Measurement Games results, or other accounts.

    To use: set RESET_COACH_PASSWORD (and COACH_EMAIL, if you have more
    than one coach account) in your host's environment variables and
    redeploy/restart. Once you've confirmed you can log in with the new
    password, remove the RESET_COACH_PASSWORD variable -- it would
    otherwise re-apply on every restart.
    """
    new_password = os.environ.get("RESET_COACH_PASSWORD")
    if not new_password:
        return
    email = os.environ.get("COACH_EMAIL")
    conn = get_conn()
    try:
        if email:
            row = conn.execute(
                "SELECT id, email FROM users WHERE role = 'coach' AND lower(email) = ?",
                (email.strip().lower(),),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT id, email FROM users WHERE role = 'coach' ORDER BY id LIMIT 1"
            ).fetchone()
        if not row:
            print("RESET_COACH_PASSWORD is set, but no matching coach account was found -- nothing changed.", flush=True)
            return
        conn.execute("UPDATE users SET password_hash = ?, is_admin = 1 WHERE id = ?", (hash_password(new_password), row["id"]))
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (row["id"],))
        conn.commit()
        print(f"RESET_COACH_PASSWORD: password updated for {row['email']} (also granted admin). "
              f"Log in with the new password, then remove the RESET_COACH_PASSWORD env var.", flush=True)
    finally:
        conn.close()
