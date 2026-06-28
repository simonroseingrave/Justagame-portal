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
    """Populate the database with a coach account, demo participants, the
    Just A Game achievement set, and a few sample activity log entries.
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

        # --- Achievements (3 per pillar + 3 milestone badges) -----------
        achievements = [
            # Physical Capability
            ("Movement Foundations", "Physical Capability",
             "Demonstrated solid athletic movement fundamentals in session.", 25),
            ("Athletic Engine", "Physical Capability",
             "Showed strong conditioning and work-rate across a full session.", 40),
            ("Power & Agility", "Physical Capability",
             "Stood out for explosive power or agility in game-based drills.", 50),
            # Game Understanding
            ("Game Reader", "Game Understanding",
             "Read the play and anticipated the right option under pressure.", 30),
            ("Tactical Thinker", "Game Understanding",
             "Applied tactical understanding to solve a game challenge.", 40),
            ("Pressure Performer", "Game Understanding",
             "Made good decisions consistently under match-like pressure.", 50),
            # Skill Adaptability
            ("Skill Explorer", "Skill Adaptability",
             "Explored new movement solutions during constraints-led drills.", 25),
            ("Adaptive Athlete", "Skill Adaptability",
             "Adapted a skill successfully to a new or changing constraint.", 40),
            ("Constraint Solver", "Skill Adaptability",
             "Consistently solved game problems through skill adaptability.", 60),
            # Confidence & Resilience
            ("Confidence Builder", "Confidence & Resilience",
             "Showed growing confidence taking on new challenges.", 25),
            ("Resilience Badge", "Confidence & Resilience",
             "Bounced back well after a setback or mistake in session.", 40),
            ("Growth Mindset", "Confidence & Resilience",
             "Embraced a tough challenge with a positive, growth-focused attitude.", 50),
            # Milestones (no single pillar)
            ("First Session Logged", "Milestone", "Completed your first logged session.", 15),
            ("5 Sessions Logged", "Milestone", "Reached 5 logged sessions.", 30),
            ("Programme Graduate", "Milestone", "Completed a full Just A Game programme.", 100),
        ]
        achievement_ids = {}
        for name, category, desc, pts in achievements:
            aid = conn.execute(
                "INSERT INTO achievements (name, category, description, points_value) VALUES (?, ?, ?, ?)",
                (name, category, desc, pts),
            ).lastrowid
            achievement_ids[name] = aid

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

        # --- Sample activity log + awards for Alex (full demo timeline) -
        alex = participant_ids["Alex Taylor"]
        sample_sessions = [
            ("2026-05-26", "Week 1 - Adaptability Programme Session", "Physical Capability",
             "Strong start, focused on athletic movement foundations under game constraints.", 10),
            ("2026-06-02", "Week 2 - Adaptability Programme Session", "Skill Adaptability",
             "Explored new ways to adapt batting technique to bowling variations.", 10),
            ("2026-06-09", "Week 3 - Adaptability Programme Session", "Game Understanding",
             "Good decision-making reading the field placements under pressure.", 10),
            ("2026-06-16", "Week 4 - Adaptability Programme Session", "Confidence & Resilience",
             "Bounced back well after a tough start to the session.", 10),
            ("2026-06-23", "Week 5 - Adaptability Programme Session", "Physical Capability",
             "Noticeable improvement in agility and footwork under fatigue.", 10),
        ]
        for date, title, category, notes, pts in sample_sessions:
            conn.execute(
                "INSERT INTO activities (participant_id, date, title, category, notes, points, logged_by, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (alex, date, title, category, notes, pts, coach_id, now()),
            )

        for ach_name, award_date in [
            ("First Session Logged", "2026-05-26"),
            ("Movement Foundations", "2026-05-26"),
            ("Skill Explorer", "2026-06-02"),
            ("Game Reader", "2026-06-09"),
            ("5 Sessions Logged", "2026-06-23"),
        ]:
            conn.execute(
                "INSERT INTO awards (participant_id, achievement_id, date_awarded, awarded_by) VALUES (?, ?, ?, ?)",
                (alex, achievement_ids[ach_name], award_date, coach_id),
            )

        # --- Lighter sample data for Jess and Sam ------------------------
        jess = participant_ids["Jess Nguyen"]
        conn.execute(
            "INSERT INTO activities (participant_id, date, title, category, notes, points, logged_by, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (jess, "2026-06-18", "1-on-1 Session with Patrick", "Skill Adaptability",
             "Worked on first-touch adaptability under pressure from different angles.", 10, coach_id, now()),
        )
        conn.execute(
            "INSERT INTO awards (participant_id, achievement_id, date_awarded, awarded_by) VALUES (?, ?, ?, ?)",
            (jess, achievement_ids["First Session Logged"], "2026-06-18", coach_id),
        )

        sam = participant_ids["Sam Wilson"]
        conn.execute(
            "INSERT INTO activities (participant_id, date, title, category, notes, points, logged_by, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (sam, "2026-06-20", "Small Group Session with Regan", "Confidence & Resilience",
             "Showed great composure leading a small group drill.", 10, coach_id, now()),
        )

        conn.commit()
        return True
    finally:
        conn.close()
