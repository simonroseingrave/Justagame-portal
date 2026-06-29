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
            "INSERT INTO users (name, email, password_hash, role, sport, programme, created_at) "
            "VALUES (?, ?, ?, 'coach', NULL, NULL, ?)",
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
            ("diamond_games", "running", 8),
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


def create_measurement_session(conn, participant_id, date, logged_by, results):
    """results: an iterable of (game_key, field_key, value) tuples, already
    filtered down to just the fields the coach actually filled in."""
    session_id = conn.execute(
        "INSERT INTO measurement_sessions (participant_id, date, logged_by, created_at) VALUES (?, ?, ?, ?)",
        (participant_id, date, logged_by, now()),
    ).lastrowid
    for game_key, field_key, value in results:
        conn.execute(
            "INSERT INTO measurement_results (session_id, game_key, field_key, value) VALUES (?, ?, ?, ?)",
            (session_id, game_key, field_key, value),
        )
    conn.commit()
    return session_id


def measurement_sessions_for(conn, participant_id):
    """All Measurement Games sessions for a participant, most recent first,
    each with its field results nested in a {(game_key, field_key): value}
    dict for easy lookup when rendering."""
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


def update_password(conn, user_id, new_password):
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(new_password), user_id),
    )
    conn.commit()


def update_profile(conn, user_id, name, email):
    conn.execute(
        "UPDATE users SET name = ?, email = ? WHERE id = ?",
        (name, email, user_id),
    )
    conn.commit()


def list_coaches(conn):
    return conn.execute(
        "SELECT * FROM users WHERE role = 'coach' ORDER BY name"
    ).fetchall()


def set_active(conn, user_id, active):
    conn.execute("UPDATE users SET active = ? WHERE id = ?", (1 if active else 0, user_id))
    conn.commit()


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
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), row["id"]))
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (row["id"],))
        conn.commit()
        print(f"RESET_COACH_PASSWORD: password updated for {row['email']}. "
              f"Log in with the new password, then remove the RESET_COACH_PASSWORD env var.", flush=True)
    finally:
        conn.close()
