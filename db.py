"""SQLite data access layer. Pure standard library (sqlite3) -- no ORM."""
import os
import sqlite3
import datetime

from auth import hash_password

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "justagame.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('coach','participant')),
    is_admin INTEGER NOT NULL DEFAULT 0,
    sport TEXT,
    programme TEXT,
    active INTEGER NOT NULL DEFAULT 1,
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
"""


def get_conn():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


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
    ]:
        try:
            conn.execute(sql)
            conn.commit()
        except Exception:
            pass  # column already exists
    conn.close()


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
            "VALUES (?, ?, ?, 'coach', 1, NULL, NULL, ?)",
            ("Coach Admin", "coach@justagame.co.nz", hash_password("CoachDemo123!"), now()),
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


def create_measurement_session(conn, participant_id, date, logged_by, results, group_id=None):
    """results: an iterable of (game_key, field_key, value) tuples, already
    filtered down to just the fields the coach actually filled in.
    group_id: the group the athlete belonged to at recording time (snapshot)."""
    session_id = conn.execute(
        "INSERT INTO measurement_sessions (participant_id, group_id, date, logged_by, created_at) VALUES (?, ?, ?, ?, ?)",
        (participant_id, group_id, date, logged_by, now()),
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


def find_or_create_session(conn, participant_id, date, logged_by, group_id=None):
    """Return the existing session id for this athlete+date, or create one.
    group_id is snapshotted on creation so the session stays attributed to
    the group the athlete was in at recording time."""
    existing = conn.execute(
        "SELECT id FROM measurement_sessions WHERE participant_id = ? AND date = ? ORDER BY id DESC LIMIT 1",
        (participant_id, date),
    ).fetchone()
    if existing:
        return existing["id"]
    return create_bare_session(conn, participant_id, date, logged_by, group_id=group_id)


def create_bare_session(conn, participant_id, date, logged_by, group_id=None):
    """Create a session with no results yet (used by quick-save flow)."""
    session_id = conn.execute(
        "INSERT INTO measurement_sessions (participant_id, group_id, date, logged_by, created_at) VALUES (?, ?, ?, ?, ?)",
        (participant_id, group_id, date, logged_by, now()),
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
    return conn.execute(
        "SELECT * FROM users WHERE role = 'coach' ORDER BY name"
    ).fetchall()


def set_admin_status(conn, user_id, is_admin):
    conn.execute("UPDATE users SET is_admin = ? WHERE id = ?", (1 if is_admin else 0, user_id))
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
    conn.execute("DELETE FROM participant_groups WHERE id = ?", (group_id,))
    conn.commit()


def assign_participant_group(conn, participant_id, group_id):
    """Set group_id for a participant. Pass None to remove from all groups."""
    conn.execute(
        "UPDATE users SET group_id = ? WHERE id = ?",
        (group_id or None, participant_id),
    )
    conn.commit()


def list_participants_by_group(conn):
    """Returns (group_groups, ungrouped) where group_groups is a list of
    (group_row, [participant_rows]) tuples ordered by group sort_order."""
    groups = list_participant_groups(conn)
    all_participants = conn.execute(
        "SELECT * FROM users WHERE role = 'participant' AND active = 1 ORDER BY name"
    ).fetchall()
    by_group = {}
    ungrouped = []
    for p in all_participants:
        gid = p["group_id"]
        if gid is None:
            ungrouped.append(p)
        else:
            by_group.setdefault(gid, []).append(p)
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


def update_resource(conn, resource_id, name, description, url, folder_id):
    conn.execute(
        "UPDATE resources SET name = ?, description = ?, url = ?, folder_id = ? WHERE id = ?",
        (name, description or None, url, folder_id or None, resource_id),
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
