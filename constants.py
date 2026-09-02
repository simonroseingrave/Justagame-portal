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

SPORTS = ["Cricket", "Football", "Hockey", "Multi-sport"]


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
                "fields": [
                    {"key": "small_ball_wall_bounce",      "label": "Small Ball - Wall Bounce",                                    "type": "number"},
                    {"key": "large_ball_wall_bounce",      "label": "Large Ball - Wall Bounce",                                    "type": "number"},
                    {"key": "small_ball_dominant",         "label": "Small Ball - Dominant Hand (Wall Bounce)",                    "type": "number"},
                    {"key": "small_ball_non_dominant",     "label": "Small Ball - Non-Dominant (Wall Bounce)",                     "type": "number"},
                    {"key": "one_foot_balance_catch",      "label": "One Foot Balance Catch - Small or Large Ball (athlete choice)",      "type": "number"},
                    {"key": "opposite_foot_balance_catch", "label": "Opposite Foot Balance Catch - Small or Large Ball (athlete choice)", "type": "number"},
                ],
            },
            {
                "key": "leap_catching_throwing",
                "name": "Grid Leap (20 attempts)",
                "fields": [
                    {"key": "points", "label": "Points", "type": "points", "unit": "out of 14"},
                ],
            },
            {
                "key": "diamond_games",
                "name": "Diamond Gates - 1 minute",
                "fields": [
                    {"key": "running_room",   "label": "Running Room (4 participants)",    "type": "number", "unit": "Number of Gates"},
                    {"key": "no_spare_gates", "label": "No Spare Gates (5 participants)",  "type": "number", "unit": "Number of Gates"},
                    {"key": "mass_running",   "label": "Mass Running (6 participants)",    "type": "number", "unit": "Number of Gates"},
                ],
            },
            {
                "key": "diamond_dribble",
                "name": "Diamond Dribble - 1 minute",
                "fields": [
                    {"key": "dribble_room",        "label": "Dribble Room (4 participants)",        "type": "number", "unit": "Number of Gates"},
                    {"key": "no_vacancy_dribbling", "label": "No Vacancy Dribbling (5 participants)", "type": "number", "unit": "Number of Gates"},
                    {"key": "mass_dribbling",       "label": "Mass Dribbling (6 participants)",      "type": "number", "unit": "Number of Gates"},
                ],
            },
            {
                "key": "diamond_gym",
                "name": "Step Up",
                "fields": [
                    {"key": "step_bench", "label": "Step / Bench Points", "type": "number", "unit": "Number of Gates"},
                ],
            },
            {
                "key": "step_over",
                "name": "Step Over",
                "fields": [
                    {"key": "low_hurdle", "label": "Low Hurdle Points", "type": "number", "unit": "Number of Gates"},
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
                "fields": [
                    {"key": "10m_front_floor",    "label": "10m Front On — Floor",             "type": "points"},
                    {"key": "10m_front_balance",  "label": "10m Front On — Balance Equipment", "type": "points"},
                    {"key": "10m_side_floor",     "label": "10m Side On — Floor",              "type": "points"},
                    {"key": "10m_side_balance",   "label": "10m Side On — Balance Equipment",  "type": "points"},
                    {"key": "20m_front_floor",    "label": "20m Front On — Floor",             "type": "points"},
                    {"key": "20m_front_balance",  "label": "20m Front On — Balance Equipment", "type": "points"},
                    {"key": "20m_side_floor",     "label": "20m Side On — Floor",              "type": "points"},
                    {"key": "20m_side_balance",   "label": "20m Side On — Balance Equipment",  "type": "points"},
                ],
            },
        ],
    },
    {
        "section": "Throw Up",
        "games": [
            {
                "key": "throw_up",
                "name": "Throw Up",
                "fields": [
                    {"key": "attempt_1", "label": "Attempt 1", "type": "points"},
                    {"key": "attempt_2", "label": "Attempt 2", "type": "points"},
                    {"key": "attempt_3", "label": "Attempt 3", "type": "points"},
                    {"key": "attempt_4", "label": "Attempt 4", "type": "points"},
                    {"key": "attempt_5", "label": "Attempt 5", "type": "points"},
                ],
                "computed": [
                    {"key": "total", "label": "Total", "type": "points",
                     "formula": "sum_of", "of": ["attempt_1", "attempt_2", "attempt_3", "attempt_4", "attempt_5"]},
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


def find_measurement_game(key):
    for game in all_measurement_games():
        if game["key"] == key:
            return game
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
