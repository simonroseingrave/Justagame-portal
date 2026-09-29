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
                "key": "balance_ball_catching",
                "name": "Balance Catching - 1 minute",
                "level": 1,
                "fields": [
                    {"key": "one_foot_balance_catch",      "label": "One Foot Balance Catch (athlete's choice of ball)",      "type": "number"},
                    {"key": "opposite_foot_balance_catch", "label": "Opposite Foot Balance Catch (athlete's choice of ball)", "type": "number"},
                    {"key": "large_ball_wall_bounce",      "label": "Large Ball - Wall Bounce",                               "type": "number"},
                    {"key": "small_ball_wall_bounce",      "label": "Small Ball - Wall Bounce",                               "type": "number"},
                ],
            },
            {
                "key": "leap_catching_throwing",
                "name": "Grid Leap — 50cm Cones (20 attempts)",
                "level": 1,
                "fields": [
                    {"key": "points", "label": "Points", "type": "points", "unit": "out of 20"},
                ],
            },
            {
                "key": "split_step",
                "name": "Split Step",
                "level": 1,
                "fields": [
                    {"key": "catches", "label": "Volleyed Catches (1 minute)", "type": "points"},
                ],
            },
            {
                "key": "diamond_games",
                "name": "Diamond Gates - 1 minute",
                "level": 1,
                "either_or": True,
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
                "fields": [
                    {"key": "small_group", "label": "Small Group (3–5 athletes)", "type": "number", "unit": "Number of Gates"},
                    {"key": "large_group", "label": "Large Group (6–8 athletes)", "type": "number", "unit": "Number of Gates"},
                ],
            },
            {
                "key": "diamond_gym",
                "name": "Step Up",
                "level": 1,
                "fields": [
                    {"key": "step_bench",      "label": "Large Ball", "type": "number", "unit": "Number of Gates"},
                    {"key": "step_bench_small", "label": "Small Ball", "type": "number", "unit": "Number of Gates"},
                ],
            },
            {
                "key": "step_over",
                "name": "Step Over",
                "level": 2,
                "fields": [
                    {"key": "low_hurdle",       "label": "Large Ball", "type": "number", "unit": "Number of Gates"},
                    {"key": "low_hurdle_small",  "label": "Small Ball", "type": "number", "unit": "Number of Gates"},
                ],
            },
        ],
    },
    {
        "section": "Throw Down",
        "games": [
            {
                "key": "throw_down",
                "name": "Throw Down",
                "level": 1,
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
    """Return MEASUREMENT_GAMES sections filtered to games up to max_level.
    If max_level is None, all games are returned (no filtering).
    """
    if max_level is None:
        return MEASUREMENT_GAMES
    result = []
    for section in MEASUREMENT_GAMES:
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
    "diamond_games",            # Diamond Gates
    "diamond_dribble",
    "diamond_gym",              # Step Up
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
        "score_fields": [
            "large_ball_wall_bounce", "small_ball_wall_bounce",
            "one_foot_balance_catch", "opposite_foot_balance_catch",
        ],
        "primary_field": "large_ball_wall_bounce",
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
    "diamond_games": {
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
    "diamond_gym": {
        "xp_type": "count",
        "multiplier": 1,
        "score_fields": ["step_bench", "step_bench_small"],
        "primary_field": "step_bench",
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
    {"label": "Bronze",   "min_xp": 200,   "colour": "#1EBE8B"},
    {"label": "Silver",   "min_xp": 1000,  "colour": "#F0A82E"},
    {"label": "Gold",     "min_xp": 5000,  "colour": "#F97316"},
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
# Sport-Specific Measurement Games
# Same structure as MEASUREMENT_GAMES but keyed by sport name.
# Add new sports here as they are defined.
SPORT_SPECIFIC_GAMES = {
    "Cricket": [
        {
            "section": "Cricket",
            "games": [
                {
                    "key": "clipncatch",
                    "name": "ClipNCatch (Catches within 1 minute)",
                    "fields": [
                        {"key": "standard_floor",     "label": "Standard Floor",     "type": "points"},
                        {"key": "balance_implement",  "label": "Balance Implement",  "type": "points"},
                    ],
                },
                {
                    "key": "straight_lofting",
                    "name": "Straight Lofting",
                    "fields": [
                        {"key": "points", "label": "Points", "type": "points"},
                    ],
                },
                {
                    "key": "under_pressure",
                    "name": "Under Pressure (gates in 1 minute)",
                    "fields": [
                        {"key": "gates", "label": "Gates", "type": "number"},
                    ],
                },
                {
                    "key": "pull_away",
                    "name": "Pull Away",
                    "fields": [
                        {"key": "points", "label": "Points", "type": "points"},
                    ],
                },
                {
                    "key": "touch_n_go",
                    "name": "Touch N Go",
                    "fields": [
                        {"key": "gates", "label": "Gates", "type": "number"},
                    ],
                },
            ],
        },
    ],
    "Touch / Rugby": [
        {
            "section": "Touch / Rugby",
            "games": [
                {
                    "key": "touch_n_go_rugby",
                    "name": "Touch N Go Rugby",
                    "fields": [
                        {"key": "gates", "label": "Gates", "type": "number"},
                    ],
                },
            ],
        },
    ],
}


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
