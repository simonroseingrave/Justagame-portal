"""SQLite data access layer. Pure standard library (sqlite3) -- no ORM."""
import os
import sqlite3
import datetime

from auth import hash_password

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "justagame.db")

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

-- Append-only level achievement record. One row per (athlete × game × level).
-- UNIQUE constraint prevents double-awarding. Never deleted.
CREATE TABLE IF NOT EXISTS level_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    game_key TEXT NOT NULL,
    level INTEGER NOT NULL,
    session_id INTEGER REFERENCES measurement_sessions(id) ON DELETE SET NULL,
    awarded_at TEXT NOT NULL,
    UNIQUE (participant_id, game_key, level)
);

-- Admin-configurable threshold per (game × level).
-- Score at or above this value earns the level.
-- For skipping_rope_sprint (lower_is_better), score at or BELOW earns the level.
CREATE TABLE IF NOT EXISTS game_level_thresholds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_key TEXT NOT NULL,
    level INTEGER NOT NULL,
    field_key TEXT NOT NULL,
    threshold_value REAL NOT NULL,
    lower_is_better INTEGER NOT NULL DEFAULT 0,
    set_by INTEGER REFERENCES users(id),
    updated_at TEXT NOT NULL,
    UNIQUE (game_key, level)
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
"""


def get_conn():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = lambda cur, row: dict(zip([d[0] for d in cur.description], row))
    conn.execute("PRAGMA foreign_keys = ON")
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
        ("diamond_games",   ["athletes_3", "athletes_4", "athletes_5"], "small_group"),
        ("diamond_games",   ["athletes_6", "athletes_7", "athletes_8"], "large_group"),
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
    ]:
        try:
            conn.execute(sql)
            conn.commit()
        except Exception:
            pass  # column already exists
    # Retroactively assign athlete numbers to any participants added before
    # this feature was introduced.
    assign_missing_athlete_numbers(conn)
    # Migrate Diamond Gates / Diamond Dribble from per-athlete-count fields to
    # small_group / large_group (idempotent: skips sessions already migrated).
    migrate_diamond_group_fields(conn)
    # Migrate role values: 'coach' with is_admin=1 → 'system_admin',
    # 'coach' with is_admin=0 → 'practitioner' (idempotent).
    migrate_roles(conn)
    conn.close()


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
            ("diamond_games", "running_room", 8),
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


def update_participant_group(conn, group_id, name, icon_url=None):
    conn.execute(
        "UPDATE participant_groups SET name = ?, icon_url = ? WHERE id = ?",
        (name, icon_url or None, group_id),
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


def update_resource(conn, resource_id, name, description, url, folder_id, self_organisation=None):
    conn.execute(
        "UPDATE resources SET name = ?, description = ?, url = ?, folder_id = ?, self_organisation = ? WHERE id = ?",
        (name, description or None, url, folder_id or None, self_organisation or None, resource_id),
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

def get_athlete_level(conn, participant_id, game_key):
    """Return the highest level the athlete has earned for a game, or 0."""
    row = conn.execute(
        "SELECT MAX(level) AS lvl FROM level_achievements WHERE participant_id = ? AND game_key = ?",
        (participant_id, game_key),
    ).fetchone()
    return row["lvl"] or 0


def get_all_athlete_levels(conn, participant_id):
    """Return dict {game_key: highest_level} for all games this athlete has levels in."""
    rows = conn.execute(
        "SELECT game_key, MAX(level) AS lvl FROM level_achievements "
        "WHERE participant_id = ? GROUP BY game_key",
        (participant_id,),
    ).fetchall()
    return {r["game_key"]: r["lvl"] for r in rows}


def award_level(conn, participant_id, game_key, level, session_id=None):
    """Award a level to an athlete. Idempotent (UNIQUE constraint, silently skips duplicates).
    Returns True if a new level was awarded, False if already held."""
    try:
        conn.execute(
            "INSERT INTO level_achievements (participant_id, game_key, level, session_id, awarded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (participant_id, game_key, level, session_id, now()),
        )
        conn.commit()
        return True
    except Exception:
        return False


# ── Level Thresholds ──────────────────────────────────────────────────────────

def get_game_threshold(conn, game_key, level):
    """Return threshold row or None. Threshold has: threshold_value, field_key, lower_is_better."""
    return conn.execute(
        "SELECT * FROM game_level_thresholds WHERE game_key = ? AND level = ?",
        (game_key, level),
    ).fetchone()


def get_all_thresholds(conn):
    """Return all threshold rows ordered by game_key, level."""
    return conn.execute(
        "SELECT * FROM game_level_thresholds ORDER BY game_key, level"
    ).fetchall()


def set_game_threshold(conn, game_key, level, field_key, threshold_value,
                       lower_is_better=False, set_by=None):
    """Insert or update a threshold. Only system_admin should call this."""
    existing = conn.execute(
        "SELECT id FROM game_level_thresholds WHERE game_key = ? AND level = ?",
        (game_key, level),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE game_level_thresholds SET field_key = ?, threshold_value = ?, "
            "lower_is_better = ?, set_by = ?, updated_at = ? WHERE id = ?",
            (field_key, threshold_value, 1 if lower_is_better else 0, set_by, now(), existing["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO game_level_thresholds "
            "(game_key, level, field_key, threshold_value, lower_is_better, set_by, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (game_key, level, field_key, threshold_value, 1 if lower_is_better else 0, set_by, now()),
        )
    conn.commit()


def delete_game_threshold(conn, game_key, level):
    conn.execute(
        "DELETE FROM game_level_thresholds WHERE game_key = ? AND level = ?",
        (game_key, level),
    )
    conn.commit()


def _check_level_thresholds(conn, participant_id, game_key, results_for_game, session_id):
    """Check if this session's results earn any new levels. Awards them and returns
    list of newly earned level ints."""
    XP_GAME_CONFIG, LEVEL_XP_AWARDS = _import_xp_constants()[:2]
    new_levels = []
    current_level = get_athlete_level(conn, participant_id, game_key)

    for target_level in range(1, 6):
        if target_level <= current_level:
            continue  # already have it
        threshold = get_game_threshold(conn, game_key, target_level)
        if not threshold:
            continue  # no threshold set yet by admin
        field_key = threshold["field_key"]
        threshold_val = threshold["threshold_value"]
        lower_is_better = bool(threshold["lower_is_better"])
        score = results_for_game.get(field_key)
        if score is None:
            continue  # this field wasn't recorded in the session
        try:
            score = float(score)
        except (TypeError, ValueError):
            continue
        earned = (score <= threshold_val) if lower_is_better else (score >= threshold_val)
        if earned:
            awarded = award_level(conn, participant_id, game_key, target_level, session_id)
            if awarded:
                new_levels.append(target_level)
                # Award XP for the level achievement
                xp_amount = LEVEL_XP_AWARDS.get(target_level, 0)
                if xp_amount:
                    award_xp(conn, participant_id, "level_achievement", xp_amount,
                             game_key=game_key, session_id=session_id,
                             notes=f"Earned Level {target_level} in {game_key}")
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


def _has_all_8_l1(conn, participant_id):
    """True if the athlete holds L1 in all 8 core games."""
    XP_GAME_CONFIG, LEVEL_XP_AWARDS, XP_RANK_TIERS, XP_PARTICIPATION, CORE_AAP_GAMES = _import_xp_constants()
    for game_key in CORE_AAP_GAMES:
        if get_athlete_level(conn, participant_id, game_key) < 1:
            return False
    return True


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

        # ── Level threshold check (formal sessions only) ──────────────────
        if is_formal:
            new_levels = _check_level_thresholds(
                conn, participant_id, game_key, game_results, session_id
            )
            for lvl in new_levels:
                xp_amt = LEVEL_XP_AWARDS.get(lvl, 0)
                awarded.append(("level_achievement", xp_amt, game_key, f"Level {lvl}"))

    # ── All 8 core games in one session bonus ─────────────────────────────
    core_in_session = _check_all_8_in_session(conn, session_id)
    if len(core_in_session) >= 8:
        if not _has_awarded_xp_type_for_session(conn, participant_id, "all_8_session", session_id):
            amt = XP_PARTICIPATION["all_8_session"]
            award_xp(conn, participant_id, "all_8_session", amt,
                     session_id=session_id, notes="All 8 core games in one session")
            awarded.append(("all_8_session", amt, None, "All 8 games bonus"))

    # ── Breadth milestone: L1 in all 8 core games ────────────────────────
    if is_formal and not _has_awarded_xp_type(conn, participant_id, "all_8_l1"):
        if _has_all_8_l1(conn, participant_id):
            amt = XP_PARTICIPATION["all_8_l1"]
            award_xp(conn, participant_id, "all_8_l1", amt,
                     session_id=session_id, notes="Earned Level 1 in all 8 core games")
            awarded.append(("all_8_l1", amt, None, "L1 all 8 games milestone"))

    total = sum(a[1] for a in awarded)
    return {
        "total_xp_awarded": total,
        "breakdown": [
            {"xp_type": a[0], "amount": a[1], "game_key": a[2], "notes": a[3]}
            for a in awarded
        ],
    }


def retroactive_xp_pass(conn):
    """One-time pass: award XP for all existing formal measurement sessions.
    Run once after deploying the XP engine. Idempotent — skips sessions that
    already have XP events. Returns count of sessions processed."""
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
