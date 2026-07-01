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
                "name": "Balance Ball Catching - 1 minute",
                "fields": [
                    {"key": "small_ball", "label": "Small Ball", "type": "number"},
                    {"key": "large_ball", "label": "Large Ball", "type": "number"},
                ],
            },
            {
                "key": "leap_catching_throwing",
                "name": "Leap Catching & Throwing - 20 attempts",
                "fields": [
                    {"key": "stationary_small_ball", "label": "Stationary Small Ball", "type": "number"},
                    {"key": "stationary_large_ball", "label": "Stationary Large Ball", "type": "number"},
                    {"key": "short_run_small_ball", "label": "Short Run Small Ball", "type": "number"},
                    {"key": "short_run_large_ball", "label": "Short Run Large Ball", "type": "number"},
                ],
            },
            {
                "key": "perception_catching",
                "name": "Perception Catching - 20 attempts",
                "fields": [
                    {"key": "very_small_ball",   "label": "Very Small Ball", "type": "number"},
                    {"key": "tape_ball",         "label": "Tape Ball",       "type": "number"},
                    {"key": "tape_ball_bounce",  "label": "Tape Ball Bounce",  "type": "number"},
                    {"key": "large_ball_taped",  "label": "Large Ball Taped",  "type": "number"},
                ],
            },
            {
                "key": "gate_dive",
                "name": "Gate Dive - 10 attempts for each",
                "fields": [
                    {"key": "walk_through_small_ball", "label": "Walk through small ball", "type": "points"},
                    {"key": "walk_through_large_ball", "label": "Walk through large ball", "type": "points"},
                    {"key": "step_over_gate_small_ball", "label": "Step Over Gate Small Ball", "type": "points"},
                    {"key": "step_over_gate_large_ball", "label": "Step Over Gate Large Ball", "type": "points"},
                ],
            },
            {
                "key": "target_shooting_passing",
                "name": "Target Shooting / Passing",
                "fields": [
                    {"key": "distance_1", "label": "Distance 1", "type": "points"},
                    {"key": "distance_2", "label": "Distance 2", "type": "points"},
                    {"key": "distance_3", "label": "Distance 3", "type": "points"},
                ],
            },
            {
                "key": "diamond_games",
                "name": "Diamond Games - 1 minute",
                "fields": [
                    {"key": "running_room",             "label": "Running Room (2 per diamond)",           "type": "number", "unit": "Number of Gates"},
                    {"key": "no_spare_gates",           "label": "No Spare Gates (4 per diamond)",         "type": "number", "unit": "Number of Gates"},
                    {"key": "mass_running",             "label": "Mass Running (6 per diamond)",           "type": "number", "unit": "Number of Gates"},
                    {"key": "no_room_running",          "label": "No Room Running (8 per diamond)",        "type": "number", "unit": "Number of Gates"},
                    {"key": "dribbling_room",           "label": "Dribbling Room (2 per diamond)",         "type": "number", "unit": "Number of Gates"},
                    {"key": "no_spare_gates_dribbling", "label": "No Spare Gates Dribbling (4 per diamond)", "type": "number", "unit": "Number of Gates"},
                    {"key": "mass_dribbling",           "label": "Mass Dribbling (6 per diamond)",         "type": "number", "unit": "Number of Gates"},
                    {"key": "no_room_dribbling",        "label": "No Room Dribbling (8 per diamond)",      "type": "number", "unit": "Number of Gates"},
                ],
            },
            {
                "key": "diamond_gym",
                "name": "Diamond Gym",
                "fields": [
                    {"key": "step_leaping_landing", "label": "Step Leaping & Landing Any Gate", "type": "number", "unit": "Number of Gates"},
                    {"key": "quarter_challenge",    "label": "Quarter Challenge",               "type": "number", "unit": "Number of Gates"},
                    {"key": "ball_carry",           "label": "Ball Carry",                      "type": "number", "unit": "Number of Gates"},
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


# Points thresholds -> level name. Must stay sorted ascending by points.
LEVELS = [
    (0, "Rookie"),
    (100, "Developing Athlete"),
    (250, "Adaptive Athlete"),
    (500, "Skilled Performer"),
    (900, "Elite Adaptor"),
]


def get_level_info(points):
    """Return dict with current level, next level, and progress fraction."""
    current_name = LEVELS[0][1]
    current_threshold = LEVELS[0][0]
    next_name = None
    next_threshold = None

    for i, (threshold, name) in enumerate(LEVELS):
        if points >= threshold:
            current_name = name
            current_threshold = threshold
            if i + 1 < len(LEVELS):
                next_threshold, next_name = LEVELS[i + 1]
            else:
                next_threshold, next_name = None, None
        else:
            break

    if next_threshold is None:
        progress = 1.0
        into_level = points - current_threshold
        span = None
    else:
        span = next_threshold - current_threshold
        into_level = points - current_threshold
        progress = max(0.0, min(1.0, into_level / span)) if span else 1.0

    return {
        "current_name": current_name,
        "current_threshold": current_threshold,
        "next_name": next_name,
        "next_threshold": next_threshold,
        "points": points,
        "points_to_next": (next_threshold - points) if next_threshold is not None else 0,
        "progress": progress,
    }
