"""Shared constants for Just A Game's Athlete Adaptability Tracking app."""

# Display name for the app -- change this in one place to rebrand everywhere
# (browser tab title, header, login page, footer, startup message).
APP_NAME = "Athlete Adaptability Tracking"

# The four development pillars used across Just A Game's coaching philosophy
# (constraints-led / athlete adaptability approach). Used as "Focus area"
# suggestions when a coach logs an activity session.
CATEGORIES = [
    "Physical Capability",
    "Game Understanding",
    "Skill Adaptability",
    "Confidence & Resilience",
]

SPORTS = ["Cricket", "Football", "Golf", "Hockey", "Multi-sport", "Netball", "Rugby", "Touch", "Volleyball"]

# Session types for Measurement Games testing.
# Each testing phase can span multiple days — coaches pick a named phase
# and a month/year rather than a specific date.
SESSION_TYPES = [
    {"key": "baseline",    "label": "Baseline Test"},
    {"key": "progress_1",  "label": "Progress Test 1"},
    {"key": "progress_2",  "label": "Progress Test 2"},
    {"key": "progress_3",  "label": "Progress Test 3"},
    {"key": "progress_4",  "label": "Progress Test 4"},
    {"key": "progress_5",  "label": "Progress Test 5"},
    {"key": "progress_6",  "label": "Progress Test 6"},
    {"key": "progress_7",  "label": "Progress Test 7"},
    {"key": "progress_8",  "label": "Progress Test 8"},
]

SESSION_LABEL_MAP = {s["key"]: s["label"] for s in SESSION_TYPES}


# ----------------------------------------------------------------------
# Measurement Games -- the structured physical-test battery coaches run
# with athletes (replaces the old achievement-badge system). Add, remove
# or change games/fields here any time; the results-entry form and the
# results history on every athlete's page are both generated from this
# list automatically, so no other code changes are needed for that.
#
# Each field has a "type" that controls how it's entered/displayed:
#   "time"   -> a stopwatch time in seconds, e.g. 4.52
#   "number" -> a plain count, e.g. catches out of attempts
#   "points" -> a scored count (entered the same way as "number", kept as
#               its own type so the on-screen wording matches the games
#               that are scored as "points" rather than raw counts)
#
# A game can also list "computed" fields -- ones a coach never types in
# directly, calculated automatically from the other fields when a session
# is saved. Right now there's one: the Skipping Rope Sprint average, which
# is the mean of Time 1/2/3 (only calculated once all three are filled in).
MEASUREMENT_GAMES = [
    {
        "section": "Timed Events",
        "games": [
            {
                "key": "skipping_rope_sprint",
                "name": "Skipping Rope Sprint (25 metres)",
                "level": 1,
                "fields": [
                    {"key": "time_1", "label": "Time 1", "type": "time"},
                    {"key": "time_2", "label": "Time 2", "type": "time"},
                    {"key": "time_3", "label": "Time 3", "type": "time"},
                ],
                "computed": [
                    {"key": "average", "label": "Average", "type": "time",
                     "formula": "average_of", "of": ["time_1", "time_2", "time_3"]},
                ],
            },
        ],
    },
    {
        "section": "Points Events",
        "games": [
            {
                # Balance Ball Catching — 1 minute
                # Fields restructured v2:
                #   large_ball_wall_bounce  → "Large Ball Two Feet (Wall Bounce)"  [ACTIVE — primary level field]
                #   one_foot_balance_catch  → "Large Ball One Foot"                [ACTIVE — single foot entry]
                #   opposite_foot_balance_catch → hidden (historical only; best-of-two computed at display time)
                #   small_ball_wall_bounce  → hidden (historical data preserved, not entered on new forms)
                "key": "balance_ball_catching",
                "name": "Balance Ball Catching",
                "level": 1,
                # level_threshold_hint: describes the primary field used for L1–L5 thresholds
                "level_threshold_hint": "Catches per minute — Large Ball Two Feet (Wall Bounce). Set thresholds for each level based on number of successful catches.",
                "fields": [
                    {"key": "large_ball_wall_bounce",      "label": "Large Ball Two Feet (Wall Bounce)",  "type": "number"},
                    {"key": "one_foot_balance_catch",      "label": "Large Ball One Foot",                "type": "number"},
                    # Hidden fields — preserved for historical data; not shown on new recording forms
                    {"key": "opposite_foot_balance_catch", "label": "Opposite Foot (historical)",         "type": "number", "hidden": True},
                    {"key": "small_ball_wall_bounce",      "label": "Small Ball Wall Bounce (historical)", "type": "number", "hidden": True},
                ],
            },
            {
                "key": "leap_catching_throwing",
                "name": "Grid Leap — 50cm Cones (20 attempts)",
                "level": 1,
                "level_threshold_hint": "Points scored out of 20 attempts. Set thresholds for each level based on successful leap-and-catch count.",
                "fields": [
                    {"key": "points", "label": "Points", "type": "points", "unit": "out of 20"},
                ],
            },
            {
                "key": "split_step",
                "name": "Split Step",
                "level": 1,
                "level_threshold_hint": "Volleyed catches in 1 minute. Set thresholds for each level based on catch count.",
                "fields": [
                    {"key": "catches", "label": "Volleyed Catches (1 minute)", "type": "points"},
                ],
            },
            {
                "key": "diamond_gates",
                "name": "Diamond Gates - 1 minute",
                "level": 1,
                "either_or": True,
                "level_threshold_hint": "Gates completed in 1 minute. Either Small Group (3–5) or Large Group (6–8) score counts — enter whichever applies. Set thresholds based on gate count.",
                "fields": [
                    {"key": "small_group", "label": "Small Group (3–5 athletes)", "type": "number", "unit": "Number of Gates"},
                    {"key": "large_group", "label": "Large Group (6–8 athletes)", "type": "number", "unit": "Number of Gates"},
                ],
            },
            {
                "key": "diamond_dribble",
                "name": "Diamond Dribble - 1 minute",
                "level": 1,
                "either_or": True,
                "level_threshold_hint": "Gates completed in 1 minute. Either Small Group (3–5) or Large Group (6–8) score counts. Set thresholds based on gate count.",
                "fields": [
                    {"key": "small_group", "label": "Small Group (3–5 athletes)", "type": "number", "unit": "Number of Gates"},
                    {"key": "large_group", "label": "Large Group (6–8 athletes)", "type": "number", "unit": "Number of Gates"},
                ],
            },
            {
                "key": "step_up",
                "name": "Step Up",
                "level": 1,
                "level_threshold_hint": "Successful step-ups in 1 minute — Large Ball only. Set thresholds for each level based on count.",
                "fields": [
                    {"key": "step_bench",       "label": "Large Ball", "type": "number", "unit": "Count"},
                    # Hidden — Small Ball no longer recorded; historical data preserved
                    {"key": "step_bench_small", "label": "Small Ball (historical)", "type": "number", "unit": "Count", "hidden": True},
                ],
            },
            {
                # Step Over — DEPRECATED. Removed from programme.
                # DB rows retained for historical reference; game hidden from all new recording forms.
                "key": "step_over",
                "name": "Step Over",
                "level": 2,
                "deprecated": True,
                "fields": [
                    {"key": "low_hurdle",      "label": "Large Ball", "type": "number", "unit": "Count"},
                    {"key": "low_hurdle_small", "label": "Small Ball", "type": "number", "unit": "Count"},
                ],
            },
        ],
    },
    {
        "section": "Throw Down",
        "games": [
            {
                # Throw Down — DEPRECATED. Removed from programme.
                # DB rows retained for historical reference; game hidden from all new recording forms.
                "key": "throw_down",
                "name": "Throw Down",
                "level": 1,
                "deprecated": True,
                "fields": [
                    {"key": "10m_front_balance", "label": "10m Front On — Balance Equipment", "type": "points"},
                ],
            },
        ],
    },
    {
        "section": "Lob Scotch",
        "games": [
            {
                "key": "lob_scotch",
                "name": "Lob Scotch",
                "level": 1,
                "fields": [
                    {"key": "squares_scored", "label": "Squares Scored", "type": "number"},
                ],
            },
        ],
    },
]


def all_measurement_games():
    """Flat list of every game dict, in display order, regardless of section."""
    games = []
    for section in MEASUREMENT_GAMES:
        games.extend(section["games"])
    return games


def max_game_level():
    """Highest level number assigned to any measurement game."""
    return max(g.get("level", 1) for g in all_measurement_games())


def games_for_max_level(max_level=None):
    """Return active (non-deprecated, non-hidden-field) game sections filtered to max_level.
    If max_level is None, all active games are returned.
    """
    source = active_measurement_games()  # already strips deprecated + hidden fields
    if max_level is None:
        return source
    result = []
    for section in source:
        filtered_games = [g for g in section["games"] if g.get("level", 1) <= max_level]
        if filtered_games:
            result.append({"section": section["section"], "games": filtered_games})
    return result


def find_measurement_game(key):
    for game in all_measurement_games():
        if game["key"] == key:
            return game
    return None


# ----------------------------------------------------------------------
# XP Engine — Athlete Engagement & Achievement System
# ----------------------------------------------------------------------

# The 8 core AAP measurement games that have full 5-level progressions
# and contribute to XP milestones (breadth bonuses, L1-all-8, etc.)
CORE_AAP_GAMES = [
    "skipping_rope_sprint",
    "balance_ball_catching",
    "leap_catching_throwing",   # Grid Leap
    "split_step",
    "diamond_gates",
    "diamond_dribble",
    "step_up",
    "lob_scotch",
]

# Per-game XP configuration.
# xp_type "count"       → score * multiplier XP awarded per session
# xp_type "improvement" → XP only on PB, 5 XP per unit_size improvement
# score_fields: all fields that can contribute a score (used for in-game XP total)
# primary_field: the single field used for PB tracking and level threshold checks
XP_GAME_CONFIG = {
    "skipping_rope_sprint": {
        "xp_type": "improvement",
        "xp_per_unit": 5,
        "unit_size": 0.1,           # seconds per XP unit
        "score_fields": ["average"],
        "primary_field": "average",
        "lower_is_better": True,
        "pb_only": True,
    },
    "balance_ball_catching": {
        "xp_type": "count",
        "multiplier": 1,
        # Active score fields only — hidden/historical fields excluded from XP calculation
        "score_fields": ["large_ball_wall_bounce", "one_foot_balance_catch"],
        # Historical one-foot fields — both checked when computing best score for display/PB
        "one_foot_fields": ["one_foot_balance_catch", "opposite_foot_balance_catch"],
        "primary_field": "large_ball_wall_bounce",   # Large Ball Two Feet — used for level thresholds
    },
    "leap_catching_throwing": {
        "xp_type": "count",
        "multiplier": 5,
        "score_fields": ["points"],
        "primary_field": "points",
    },
    "split_step": {
        "xp_type": "count",
        "multiplier": 1,
        "score_fields": ["catches"],
        "primary_field": "catches",
    },
    "diamond_gates": {
        "xp_type": "count",
        "multiplier": 5,
        "score_fields": ["small_group", "large_group"],
        "primary_field": "small_group",
    },
    "diamond_dribble": {
        "xp_type": "count",
        "multiplier": 5,
        "score_fields": ["small_group", "large_group"],
        "primary_field": "small_group",
    },
    "step_up": {
        "xp_type": "count",
        "multiplier": 1,
        # step_bench_small hidden from new forms; excluded from active XP calculation
        "score_fields": ["step_bench"],
        "primary_field": "step_bench",   # Large Ball — used for level thresholds
    },
    "lob_scotch": {
        "xp_type": "count",
        "multiplier": 5,
        "score_fields": ["squares_scored"],
        "primary_field": "squares_scored",
    },
}

# XP awarded when an athlete earns a level achievement (one-time, permanent)
LEVEL_XP_AWARDS = {1: 100, 2: 200, 3: 350, 4: 500, 5: 750}

# Rank tiers (ascending by min_xp). label, min_xp, hex colour
XP_RANK_TIERS = [
    {"label": "Starter",  "min_xp": 0,     "colour": "#6E737B"},
    {"label": "Bronze",   "min_xp": 2000,  "colour": "#1EBE8B"},
    {"label": "Silver",   "min_xp": 5000,  "colour": "#F0A82E"},
    {"label": "Gold",     "min_xp": 10000, "colour": "#F97316"},
    {"label": "Titanium", "min_xp": 15000, "colour": "#8B5CF6"},
]

# Flat XP award amounts for participation events
XP_PARTICIPATION = {
    "formal_game":       50,   # completing one game in a formal test session
    "self_directed_game": 25,  # completing one game in a self-directed session
    "pb_formal":         50,   # personal best in a formal session
    "pb_self_directed":  25,   # personal best in a self-directed session
    "welcome_bonus":     100,  # first ever session
    "first_game":        20,   # first time ever playing a specific game
    "all_8_session":     100,  # all 8 core games completed in one session
    "streak_3":          30,   # 3-session attendance streak
    "streak_5":          75,   # 5-session attendance streak
    "all_8_l1":          500,  # earned L1 in all 8 core games (cumulative milestone)
    "milestone_10":      150,  # 10th attended session
    "milestone_25":      300,  # 25th attended session
    "milestone_50":      600,  # 50th attended session
}


def get_athlete_rank_tier(total_xp):
    """Return the rank tier dict for a given total XP value."""
    tier = XP_RANK_TIERS[0]
    for t in XP_RANK_TIERS:
        if total_xp >= t["min_xp"]:
            tier = t
    return tier


def get_next_rank_tier(total_xp):
    """Return the next rank tier dict (or None if at Titanium)."""
    for i, t in enumerate(XP_RANK_TIERS):
        if total_xp < t["min_xp"]:
            return t
    return None


# ----------------------------------------------------------------------
# Game Display Names — canonical short names used in reports, athlete
# dashboard, threshold admin UI, and any user-facing copy.
# Internal DB keys are kept stable; display names live here.
# ----------------------------------------------------------------------
GAME_DISPLAY_NAMES = {
    "skipping_rope_sprint":   "Skipping Rope Sprint",
    "balance_ball_catching":  "Balance Ball Catching",
    "leap_catching_throwing": "Grid Leap",
    "split_step":             "Split Step",
    "diamond_gates":          "Diamond Gates",
    "diamond_dribble":        "Diamond Dribble",
    "step_up":                "Step Up",
    "lob_scotch":             "Lob Scotch",
    # Deprecated games — kept for historical display
    "step_over":              "Step Over",
    "throw_down":             "Throw Down",
}

# Per-game level progression descriptions used in athlete reports and
# the threshold admin UI. Indexed by game_key → list of 5 strings (L1–L5).
# Practitioners read these when setting thresholds so they know what
# score target to enter for each level.
GAME_LEVEL_DESCRIPTIONS = {
    "skipping_rope_sprint": [
        "L1 — Completes 25m with consistent rope rhythm",
        "L2 — Achieving a solid average time across 3 runs",
        "L3 — Consistent speed; minimal time variance between runs",
        "L4 — Strong pace; approaching personal ceiling",
        "L5 — Elite speed with full rope control across all 3 runs",
    ],
    "balance_ball_catching": [
        "L1 — Catching reliably on two feet from a wall bounce",
        "L2 — Two-feet catching consistent; beginning single-foot control",
        "L3 — Single-foot catches achieved on preferred side",
        "L4 — Single-foot catches on both sides; increasing difficulty",
        "L5 — High-volume catching on either foot with control",
    ],
    "leap_catching_throwing": [
        "L1 — Landing and returning with basic control (out of 20)",
        "L2 — Consistent catching and throwing rhythm through cones",
        "L3 — Smooth transitions; increasing points per attempt",
        "L4 — High success rate across all 20 attempts",
        "L5 — Near-maximum points with full athletic expression",
    ],
    "split_step": [
        "L1 — Initiating split step before each catch",
        "L2 — Timing improving; catches per minute increasing",
        "L3 — Consistent split step rhythm with good catch count",
        "L4 — High catch volume; reading and reacting to ball",
        "L5 — Elite reaction and volley count in 1 minute",
    ],
    "diamond_gates": [
        "L1 — Moving through gates with awareness of group",
        "L2 — Increasing gate count; reading the diamond shape",
        "L3 — Smooth movement; consistent gate count per minute",
        "L4 — High gate count with decision-making under pressure",
        "L5 — Maximum gates; leading and adapting within the group",
    ],
    "diamond_dribble": [
        "L1 — Dribbling through gates with basic ball control",
        "L2 — Gate count increasing; fewer losses of possession",
        "L3 — Smooth dribbling; consistent count across the diamond",
        "L4 — High gate count with close ball control",
        "L5 — Elite gate count; full ball mastery in group context",
    ],
    "step_up": [
        "L1 — Completing step-ups with large ball control",
        "L2 — Increasing step-up count; rhythm developing",
        "L3 — Consistent step-up count; strong balance",
        "L4 — High step-up volume with full control",
        "L5 — Maximum step-ups; elite balance and coordination",
    ],
    "lob_scotch": [
        "L1 — Scoring squares with basic lob trajectory",
        "L2 — Increasing squares scored; trajectory improving",
        "L3 — Consistent scoring; adapting angle and power",
        "L4 — High square count; reading the grid confidently",
        "L5 — Maximum squares; elite lob control and placement",
    ],
}


# ----------------------------------------------------------------------
# Helper: active_measurement_games()
# Returns MEASUREMENT_GAMES sections filtered to exclude:
#   - deprecated games (deprecated=True) → removed from programme
#   - hidden fields within active games → not entered on new forms
# Historical data for these games/fields remains in the DB and is
# still queryable for display; only new data entry is blocked.
# ----------------------------------------------------------------------
def active_measurement_games():
    """Return MEASUREMENT_GAMES with deprecated games removed and hidden fields stripped."""
    result = []
    for section in MEASUREMENT_GAMES:
        active_games = []
        for game in section["games"]:
            if game.get("deprecated"):
                continue
            # Strip hidden fields — keep computed fields and all non-hidden
            active_fields = [f for f in game.get("fields", []) if not f.get("hidden")]
            active_game = dict(game)
            active_game["fields"] = active_fields
            active_games.append(active_game)
        if active_games:
            result.append({"section": section["section"], "games": active_games})
    return result


def all_active_measurement_games():
    """Flat list of active game dicts (no deprecated, hidden fields stripped).
    Use wherever all_measurement_games() was used for display/history rendering.
    """
    return [game for section in active_measurement_games() for game in section["games"]]


def best_one_foot_score(session_data):
    """Return the best single-foot Balance Ball Catching score from a session dict.

    Handles both old data (one_foot_balance_catch + opposite_foot_balance_catch)
    and new single-field data (one_foot_balance_catch only).
    Returns None if no one-foot data exists.
    """
    cfg = XP_GAME_CONFIG.get("balance_ball_catching", {})
    one_foot_fields = cfg.get("one_foot_fields", ["one_foot_balance_catch", "opposite_foot_balance_catch"])
    scores = []
    for field in one_foot_fields:
        val = session_data.get(field)
        if val is not None:
            try:
                scores.append(float(val))
            except (TypeError, ValueError):
                pass
    return max(scores) if scores else None


# ----------------------------------------------------------------------
# Sport-Specific Measurement Games
# Same structure as MEASUREMENT_GAMES but keyed by sport name.
# Parked for next build stage — sport-specific games will be added here
# when the donor sport programme is ready to launch.
SPORT_SPECIFIC_GAMES = {}


def all_sport_games(sport):
    """Flat list of every game dict for a given sport."""
    games = []
    for section in SPORT_SPECIFIC_GAMES.get(sport, []):
        games.extend(section["games"])
    return games


def find_sport_game(key):
    """Find a sport-specific game by key across all sports."""
    for sport_sections in SPORT_SPECIFIC_GAMES.values():
        for section in sport_sections:
            for game in section["games"]:
                if game["key"] == key:
                    return game
    return None


def find_any_game(key):
    """Find a game by key in base games or any sport-specific games."""
    return find_measurement_game(key) or find_sport_game(key)


# Improvement % thresholds -> level name.
# Based on average % improvement across all measurement game fields
# between an athlete's first and latest recorded session.
# Must stay sorted ascending by percentage.
IMPROVEMENT_LEVELS = [
    (0,  "Baseline Set"),
    (1,  "Early Gains"),
    (10, "Building Adaptability"),
    (20, "Adaptive Athlete"),
    (30, "Skilled Performer"),
    (40, "Elite Adaptor"),
]

# Maximum % improvement that fills the bar to 100%
IMPROVEMENT_MAX_PCT = 40


def get_improvement_level(pct):
    """Return level info dict from an average improvement percentage.

    pct=None means only one session recorded (baseline set, no comparison yet).
    """
    if pct is None:
        return {
            "name": "Baseline Set",
            "progress": 0.0,
            "pct": None,
            "next_name": "Early Gains",
            "next_threshold": 1,
            "current_threshold": 0,
            "baseline_only": True,
        }

    current_name = IMPROVEMENT_LEVELS[0][1]
    current_threshold = IMPROVEMENT_LEVELS[0][0]
    next_name = None
    next_threshold = None

    for i, (threshold, name) in enumerate(IMPROVEMENT_LEVELS):
        if pct >= threshold:
            current_name = name
            current_threshold = threshold
            if i + 1 < len(IMPROVEMENT_LEVELS):
                next_threshold, next_name = IMPROVEMENT_LEVELS[i + 1]
            else:
                next_threshold, next_name = None, None
        else:
            break

    if next_threshold is None:
        progress = 1.0
    else:
        span = next_threshold - current_threshold
        into_level = pct - current_threshold
        progress = max(0.0, min(1.0, into_level / span)) if span else 1.0

    return {
        "name": current_name,
        "progress": progress,
        "pct": pct,
        "next_name": next_name,
        "next_threshold": next_threshold,
        "current_threshold": current_threshold,
        "baseline_only": False,
    }


# ── Scoring Areas ─────────────────────────────────────────────────────────────
# Canonical list of all individually scored entities shown in the score
# distribution report, threshold admin, and athlete level grid.
#
# field_key = None  → "pooled" game: all score_fields from XP_GAME_CONFIG are
#                     combined for the distribution, and any one of them meeting
#                     the threshold earns the level. The threshold is stored in
#                     game_level_thresholds using the primary (first) score_field.
# field_key = str   → single-field area, including both Balance Ball variants
#                     which share a game_key but have separate achievements.
SCORING_AREAS = [
    {
        "display_name": "Skipping Rope Sprint",
        "game_key":     "skipping_rope_sprint",
        "field_key":    "average",
        "lower_is_better": True,
    },
    {
        "display_name": "Balance Ball — Two Feet",
        "game_key":     "balance_ball_catching",
        "field_key":    "large_ball_wall_bounce",
        "lower_is_better": False,
    },
    {
        "display_name": "Balance Ball — One Foot",
        "game_key":     "balance_ball_catching",
        "field_key":    "one_foot_balance_catch",
        "lower_is_better": False,
    },
    {
        "display_name": "Grid Leap",
        "game_key":     "leap_catching_throwing",
        "field_key":    "points",
        "lower_is_better": False,
    },
    {
        "display_name": "Split Step",
        "game_key":     "split_step",
        "field_key":    "catches",
        "lower_is_better": False,
    },
    {
        "display_name": "Diamond Gates",
        "game_key":     "diamond_gates",
        "field_key":    None,   # pooled: small_group + large_group combined
        "lower_is_better": False,
    },
    {
        "display_name": "Diamond Dribble",
        "game_key":     "diamond_dribble",
        "field_key":    None,   # pooled: small_group + large_group combined
        "lower_is_better": False,
    },
    {
        "display_name": "Step Up",
        "game_key":     "step_up",
        "field_key":    "step_bench",
        "lower_is_better": False,
    },
    {
        "display_name": "Lob Scotch",
        "game_key":     "lob_scotch",
        "field_key":    "squares_scored",
        "lower_is_better": False,
    },
]

def threshold_field_key(area):
    """Return the field_key used to store/retrieve thresholds for a scoring area.
    Pooled areas store against the primary score_field from XP_GAME_CONFIG."""
    if area["field_key"] is not None:
        return area["field_key"]
    cfg = XP_GAME_CONFIG.get(area["game_key"], {})
    fields = cfg.get("score_fields", [])
    return fields[0] if fields else ""


# ── S&C Gap Language ──────────────────────────────────────────────────────────
# Per-scoring-area S&C gap descriptions and programme recommendations.
# Keyed by (game_key, stored_field_key) — use threshold_field_key(area) to get stored_field_key.
# Used in the individual athlete report to generate S&C-language gap analysis.

SC_GAP_LANGUAGE = {
    ("balance_ball_catching", "large_ball_wall_bounce"): {
        "display": "Balance Catching — Two Feet",
        "family": "Balance & Postural Control",
        "sc_gap": (
            "Bilateral balance deficit — the proprioceptive system is not adequately "
            "managing postural stability under a dual-task demand (balance + catch). "
            "The stable base required to support a secondary perceptual demand is not yet established."
        ),
        "sc_programme": (
            "Prioritise bilateral proprioceptive loading: single-plane balance holds progressing "
            "to unstable surfaces. Include wall-supported catching as a controlled dual-task. "
            "Avoid premature loading on unstable surfaces — build a stable base first. "
            "Calf and ankle stability work underpins the postural hold."
        ),
        "d2_focus": ["Bilateral balance", "Proprioception", "Perceptual-action coupling"],
        "athlete_what": "Staying balanced while catching is something to develop — when your base is solid, everything else gets easier.",
        "athlete_why": "In your sport, staying steady when a ball comes to you — or when someone puts you under pressure — makes a real difference. This is the foundation.",
        "athlete_games": ["Balance Ball Catching (self-test)", "Lob Scotch", "Step Up"],
        "athlete_sc": "Try standing on two feet and catching a ball thrown against a wall. As you get better, close your eyes for a second before each catch to make it harder.",
    },
    ("balance_ball_catching", "one_foot_balance_catch"): {
        "display": "Balance Catching — One Foot",
        "family": "Balance & Postural Control",
        "sc_gap": (
            "Unilateral balance deficit — single-leg proprioceptive control is insufficient "
            "to support a secondary perceptual demand. The athlete cannot yet stabilise on "
            "one foot while simultaneously tracking and catching a ball."
        ),
        "sc_programme": (
            "Build unilateral proprioceptive control progressively: single-leg holds → "
            "single-leg with arm reach → single-leg catch. Only introduce unstable surfaces "
            "once stable ground control is consistent. Hip abductor and ankle stability "
            "work (single-leg deadlifts, lateral band walks) directly supports this area."
        ),
        "d2_focus": ["Unilateral balance", "Proprioception", "Perceptual-action coupling"],
        "athlete_what": "Balancing on one leg while tracking a ball is a real skill — and it's very trainable.",
        "athlete_why": "Most sport happens on one leg — cutting, landing, holding your position. Getting comfortable here makes you more robust and harder to knock off balance.",
        "athlete_games": ["Balance Ball Catching (self-test)", "Step Up", "Grid Leap"],
        "athlete_sc": "Practice standing on one leg for 30 seconds at a time — once that's easy, try catching a ball while you do it. Simple but effective.",
    },
    ("lob_scotch", "squares_scored"): {
        "display": "Lob Scotch",
        "family": "Explosive & Landing",
        "sc_gap": (
            "Dynamic landing mechanics deficit — inadequate bilateral landing control "
            "following a unilateral projective movement. Landing absorption and re-stabilisation "
            "from the hop-to-land transition is underdeveloped."
        ),
        "sc_programme": (
            "Focus on progressive landing mechanics: drop landings → box step-offs → "
            "unilateral hops to bilateral landing. Cue knee-over-toe alignment and full "
            "ankle dorsiflexion on contact. Avoid max-effort hops until controlled, "
            "quiet landing is consistent. Eccentric quad and glute strength underpins "
            "the absorption capacity."
        ),
        "d2_focus": ["Landing mechanics", "Plyometric power", "Rhythmic coordination"],
        "athlete_what": "Your jumping rhythm and landing control is something to work on — you're building the foundation for real explosive movement.",
        "athlete_why": "Being able to hop, land softly, and rebalance quickly shows up in every sport — jumping for a ball, landing after a contest, changing direction at speed.",
        "athlete_games": ["Lob Scotch (self-test)", "Grid Leap", "Step Up"],
        "athlete_sc": "Practice small, controlled hops — jump and stick the landing for 2 seconds before jumping again. Focus on landing quietly, knees soft.",
    },
    ("leap_catching_throwing", "points"): {
        "display": "Grid Leap",
        "family": "Explosive & Landing",
        "sc_gap": (
            "Horizontal power and spatial targeting deficit — inadequate projective force "
            "production and/or landing accuracy under a concurrent perceptual demand. "
            "The athlete cannot yet couple horizontal force output with simultaneous ball "
            "tracking and spatial target awareness."
        ),
        "sc_programme": (
            "Develop horizontal power with landing accuracy together: broad jumps to a "
            "target zone, medicine ball horizontal throws for force production. Progress "
            "to reactive catch-and-jump sequences. Include spatial target work alongside "
            "power development — accuracy and distance should develop in parallel, not in series."
        ),
        "d2_focus": ["Horizontal power", "Landing mechanics", "Perceptual-action coupling"],
        "athlete_what": "Combining a big leap with a catch and throw is tough — this is an exciting area to develop because the gains are very visible.",
        "athlete_why": "Leaping to take a mark, jumping to intercept, or driving through space under pressure — this is where physical power meets game reading.",
        "athlete_games": ["Grid Leap (self-test)", "Diamond Gates", "Lob Scotch"],
        "athlete_sc": "Broad jumps are great here — jump as far as you can and focus on landing in balance. Then try catching something at the same time.",
    },
    ("step_up", "step_bench"): {
        "display": "Step Up",
        "family": "Explosive & Landing",
        "sc_gap": (
            "Vertical force production with concurrent hand-eye coordination deficit — "
            "step-up rhythm and catch timing are decoupled. The athlete cannot yet maintain "
            "the full perception-action loop through the complete vertical movement cycle."
        ),
        "sc_programme": (
            "Build step-up rhythm before adding the ball: metronome-paced step-ups, "
            "focusing on full hip extension at the top position. Once rhythm is consistent, "
            "introduce the self-feed wall catch. Vertical power foundation work (box step-ups, "
            "loaded step-ups, calf raises) supports the locomotor demand and reduces "
            "cognitive load on the movement pattern."
        ),
        "d2_focus": ["Vertical power", "Rhythmic coordination", "Perceptual-action coupling"],
        "athlete_what": "Keeping your rhythm while doing two things at once — stepping and catching — is a great skill to build.",
        "athlete_why": "Athletes who can keep moving consistently while tracking a ball have a real edge. This tests whether your body can run on autopilot so your mind can focus on the game.",
        "athlete_games": ["Step Up (self-test)", "Skipping Rope Sprint", "Diamond Gates"],
        "athlete_sc": "Box step-ups are a simple gym exercise that directly helps here — focus on driving all the way up to a full hip extension at the top.",
    },
    ("skipping_rope_sprint", "average"): {
        "display": "Skipping Rope Sprints",
        "family": "Dynamic Locomotor",
        "sc_gap": (
            "Linear speed with rhythmic coordination deficit — the athlete cannot yet "
            "synchronise locomotion with rope rotation at sufficient pace. Sprint mechanics "
            "and rope timing are not coupled, with the rope constraint reducing the efficiency "
            "of the locomotor pattern."
        ),
        "sc_programme": (
            "Address sprint mechanics and rope coordination as separate qualities before "
            "combining them. For the S&C component: acceleration work (wall drives, A-skips, "
            "resisted sprint starts) builds the speed foundation. Progress to combined "
            "rope-sprint sets once each element is consistent in isolation. "
            "Note: this is an inverse metric — lower time is better."
        ),
        "d2_focus": ["Linear speed", "Rhythmic coordination"],
        "athlete_what": "Your running speed and coordination under a constraint is something to develop — and it responds really well to practice.",
        "athlete_why": "Pure speed is one of the most valuable things in sport. Getting faster over short distances — and staying coordinated while you do it — is a game-changer.",
        "athlete_games": ["Skipping Rope Sprint (self-test)", "Diamond Gates", "Diamond Dribble"],
        "athlete_sc": "Acceleration drills are the best gym support here — wall drive holds, A-skips, short sprint starts from standing. Focus on the first 5 metres.",
    },
    ("diamond_gates", "small_group"): {
        "display": "Diamond Gates",
        "family": "Dynamic Locomotor",
        "sc_gap": (
            "Change of direction speed deficit — the athlete is not efficiently navigating "
            "the spatial structure of the diamond under the group time constraint. "
            "Deceleration mechanics, re-acceleration, and turning efficiency need development."
        ),
        "sc_programme": (
            "COD speed development: deceleration mechanics first (hip-sink, foot-strike "
            "positioning), then 5-10-5 shuttle progressions, lateral shuffle to sprint "
            "transitions. Strength base directly supports deceleration capacity — include "
            "rear-foot-elevated split squats and lateral band work for hip abductor control "
            "in the change-of-direction moment."
        ),
        "d2_focus": ["Change of direction speed", "Reactive agility"],
        "athlete_what": "Changing direction quickly and efficiently is something to keep working on — this is one of the most impactful areas in field and court sports.",
        "athlete_why": "The ability to stop, change direction and accelerate again quickly is at the heart of getting to the right place before anyone else.",
        "athlete_games": ["Diamond Gates (self-test & programme)", "Diamond Dribble", "Split Step"],
        "athlete_sc": "Shuttle runs are your friend — short, sharp, and frequent. Focus on the deceleration (the slow-down before you turn) as much as the sprint.",
    },
    ("diamond_dribble", "small_group"): {
        "display": "Diamond Dribble",
        "family": "Dynamic Locomotor",
        "sc_gap": (
            "Change of direction speed with concurrent ball manipulation deficit — "
            "the dribble constraint is absorbing perceptual and motor resources, "
            "reducing locomotor efficiency. Dual-task capacity (movement quality + "
            "ball control) is underdeveloped."
        ),
        "sc_programme": (
            "From an S&C perspective, address movement quality as the priority: COD "
            "mechanics, deceleration control, and unilateral leg strength (split squats, "
            "lateral lunges). Ball manipulation is a skill quality developed separately. "
            "Combine only once the movement pattern is sufficiently automatic that it "
            "no longer competes for attentional resources."
        ),
        "d2_focus": ["Change of direction speed", "Ball manipulation", "Ball-foot perceptual coupling"],
        "athlete_what": "Moving quickly with the ball while changing direction is something to develop — your movement and ball control will start to click together.",
        "athlete_why": "Being able to move with the ball without thinking about it frees your mind to read the game. This area is about making ball movement feel automatic.",
        "athlete_games": ["Diamond Dribble (self-test & programme)", "Diamond Gates", "Skipping Rope Sprint"],
        "athlete_sc": "Work on your change-of-direction movement without the ball first — get sharp at stopping and starting. Then bring the ball back in.",
    },
    ("split_step", "catches"): {
        "display": "Split Step",
        "family": "Perceptual-Motor Speed",
        "sc_gap": (
            "Reactive agility deficit — the athlete is not intercepting the reflex ball "
            "within the available temporal window at sufficient rate. Reactive speed and "
            "the coupling between visual stimulus and motor response are limiting performance."
        ),
        "sc_programme": (
            "Reactive agility training: visual stimulus to movement response drills, "
            "1v1 mirroring, partner signal COD. Plyometric base supports reactive speed — "
            "include drop-catch drills and rapid ground contact (pogo) work to reduce "
            "ground contact time. Critically: avoid choreographed agility patterns. "
            "The S&C adaptation must occur under genuine unpredictability to transfer."
        ),
        "d2_focus": ["Reactive agility", "Perceptual-action coupling"],
        "athlete_what": "Reacting quickly to a ball that you can't predict is something to sharpen — this is one of the most sport-specific skills there is.",
        "athlete_why": "The best athletes read play early and move before anyone else. This test measures exactly that — your ability to pick up cues and react instantly.",
        "athlete_games": ["Split Step (self-test)", "Split Decision", "Diamond Gates"],
        "athlete_sc": "Play reaction games with a partner — they point a direction, you move. Or drop-catch drills: hold a ball at shoulder height, drop it, catch before it bounces twice.",
    },
}
