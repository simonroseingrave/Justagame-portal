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
                # Straight hopscotch pattern. Dot spacing and square count vary by level:
                #   L1: 50 cm · 12 squares   L2: 50 cm · 15 squares   L3: 50 cm · 15 squares
                #   L4: 60 cm · 12 squares   L5: 75 cm · 12 squares
                "level_setups": {
                    1: "50 cm dots · 12 squares · max score 12",
                    2: "50 cm dots · 15 squares · max score 15",
                    3: "50 cm dots · 15 squares · max score 15",
                    4: "60 cm dots · 15 squares · max score 15",
                    5: "75 cm dots · 15 squares · max score 15",
                },
                "fields": [
                    {"key": "squares_scored", "label": "Squares Claimed", "type": "number"},
                ],
            },
        ],
    },
    {
        "section": "Lateral Ladder",
        "games": [
            {
                "key": "lateral_ladder",
                "name": "Lateral Ladder - 1 minute",
                "level": 1,
                # Lateral skater leap pattern. Two parallel lines 1.5 m apart; dots along
                # each line vary by level (rung spacing = longitudinal dot spacing).
                # Timed: 1 minute. Score = total dots claimed (2 per rung). 12 rungs at all levels.
                # L1: 0.5 m spacing (6 m course) · max 24  L2: 0.5 m · max 24
                # L3: 0.75 m spacing (9 m course) · max 24  L4: 1.0 m (12 m course) · max 24
                # L5: 1.25 m spacing (15 m course) · max 24
                "level_threshold_hint": "Dots claimed in 1 minute. Athlete returns to Start if they miss a dot or drop the ball. Set thresholds for each level based on dot count (max 24).",
                "level_setups": {
                    1: "0.5 m rung spacing · 6 m course · 12 rungs · max 24 dots",
                    2: "0.5 m rung spacing · 6 m course · 12 rungs · max 24 dots",
                    3: "0.75 m rung spacing · 9 m course · 12 rungs · max 24 dots",
                    4: "1.0 m rung spacing · 12 m course · 12 rungs · max 24 dots",
                    5: "1.25 m rung spacing · 15 m course · 12 rungs · max 24 dots",
                },
                "fields": [
                    {"key": "dots_claimed", "label": "Dots Claimed (1 minute)", "type": "number"},
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
    "lateral_ladder",
]

# Per-game XP configuration.
# primary_field: the single field used for improvement % calculation in testing rounds.
# higher_is_better: True  → improvement = (new - old) / old * 100
#                   False → improvement = (old - new) / old * 100  (e.g. timing games)
# score_fields: all fields recorded in a testing round session.
XP_GAME_CONFIG = {
    "skipping_rope_sprint": {
        "score_fields": ["average"],
        "primary_field": "average",
        "higher_is_better": False,   # lower time = better
    },
    "balance_ball_catching": {
        # Active score fields only — hidden/historical fields excluded
        "score_fields": ["large_ball_wall_bounce", "one_foot_balance_catch"],
        "one_foot_fields": ["one_foot_balance_catch", "opposite_foot_balance_catch"],
        "primary_field": "large_ball_wall_bounce",
        "higher_is_better": True,
    },
    "leap_catching_throwing": {
        "score_fields": ["points"],
        "primary_field": "points",
        "higher_is_better": True,
    },
    "split_step": {
        "score_fields": ["catches"],
        "primary_field": "catches",
        "higher_is_better": True,
    },
    "diamond_gates": {
        "score_fields": ["small_group", "large_group"],
        "primary_field": "small_group",
        "higher_is_better": True,
    },
    "diamond_dribble": {
        "score_fields": ["small_group", "large_group"],
        "primary_field": "small_group",
        "higher_is_better": True,
    },
    "step_up": {
        # step_bench_small hidden from new forms
        "score_fields": ["step_bench"],
        "primary_field": "step_bench",
        "higher_is_better": True,
    },
    "lob_scotch": {
        "score_fields": ["squares_scored"],
        "primary_field": "squares_scored",
        "higher_is_better": True,
    },
    "lateral_ladder": {
        "score_fields": ["dots_claimed"],
        "primary_field": "dots_claimed",
        "higher_is_better": True,
    },
}

# AXP per testing round (see db.py award_round_xp)
# Baseline round: flat participation AXP per game completed + completion bonus
ROUND_XP_BASELINE_PER_GAME = 25    # per game recorded in a baseline round
ROUND_XP_COMPLETION_BONUS   = 50   # bonus for completing all 8 core games in a round
# Re-test round: improvement % × ROUND_XP_IMPROVEMENT_FACTOR per game, capped at max
ROUND_XP_IMPROVEMENT_FACTOR = 6    # improvement_pct × 6 AXP per game
ROUND_XP_IMPROVEMENT_CAP    = 150  # max AXP per game per re-test round

# Kept as empty dict so legacy imports in db.py / views.py don't crash.
# Automatic level-up XP from session recording is disabled — levels are now
# controlled exclusively through testing rounds (see testing_rounds table).
LEVEL_XP_AWARDS = {}

# Rank tiers (ascending by min_xp). label, min_xp, hex colour
XP_RANK_TIERS = [
    {"label": "Explorer",   "min_xp": 0,     "colour": "#6E737B"},
    {"label": "Discoverer", "min_xp": 3000,  "colour": "#CD7F32"},
    {"label": "Adapter",    "min_xp": 6500,  "colour": "#A0A9B8"},
    {"label": "Connector",  "min_xp": 11000, "colour": "#F3AA33"},
    {"label": "Attuned",    "min_xp": 17000, "colour": "#5EEAD4"},
    {"label": "Dynamic",    "min_xp": 25000, "colour": "#8B5CF6"},
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
    """Return the next rank tier dict (or None if at Dynamic)."""
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
    "lateral_ladder":         "Lateral Ladder",
    # Deprecated games — kept for historical display
    "step_over":              "Step Over",
    "throw_down":             "Throw Down",
}

# ── Card Taxonomy ────────────────────────────────────────────────────────────
# Maps card slug (from card_data.py) → taxonomy dimensions D1–D9 + game_keys.
# game_keys = list of game_key strings for resource_game_links (D10).
# Used by db.sync_card_taxonomy() to auto-tag resources when a card_slug is set.
# Re-generate with: cd outputs && python3 -c "from card_data import ALL_CARDS; ..."
CARD_TAXONOMY = {
    'balance-catching': {
        'D1': ['Balance & Postural Control'],
        'D2': ['Bilateral Balance', 'Unilateral Balance', 'Proprioception', 'Hand-Eye Coordination'],
        'D3': ['Perception-Action Coupling', 'Postural Attunement', 'Self-Organisation', 'Repetition Without Repetition'],
        'D4': ['Alternating'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Bosu / Balance Ball', 'Large Ball', 'Small Ball', 'Wall'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Individual'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'game_keys': ['balance_ball_catching'],
    },
    'lob-scotch': {
        'D1': ['Balance & Postural Control'],
        'D2': ['Unilateral Balance', 'Rhythmic Coordination', 'Hand-Eye Coordination', 'Proprioception'],
        'D3': ['Perception-Action Coupling', 'Postural Attunement', 'Self-Organisation', 'Repetition Without Repetition'],
        'D4': ['Unilateral', 'Alternating'],
        'D5': ['Task'],
        'D6': ['Small Ball', 'Gate / Cone'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Individual'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'game_keys': ['lob_scotch'],
    },
    'lob-scotch-partner-feed': {
        'D1': ['Balance & Postural Control'],
        'D2': ['Unilateral Balance', 'Rhythmic Coordination', 'Hand-Eye Coordination', 'Proprioception'],
        'D3': ['Perception-Action Coupling', 'Postural Attunement', 'Self-Organisation', 'Interpersonal Coordination'],
        'D4': ['Unilateral', 'Alternating'],
        'D6': ['Small Ball', 'Large Ball', 'Gate / Cone'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Pair'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'game_keys': ['lob_scotch'],
    },
    'skipping-rope-relay': {
        'D1': ['Dynamic Locomotor'],
        'D2': ['Rhythmic Coordination', 'Linear Speed', 'Plyometric Power'],
        'D3': ['Constrain to Afford', 'Interpersonal Coordination', 'Repetition Without Repetition', 'Functional Variability'],
        'D4': ['Bilateral'],
        'D6': ['Standard Rope'],
        'D7': ['Large 15m+'],
        'D8': ['Pair', 'Small Group 3–5'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'game_keys': ['skipping_rope_sprint'],
    },
    'skipping-rope-sprint': {
        'D1': ['Dynamic Locomotor'],
        'D2': ['Rhythmic Coordination', 'Linear Speed', 'Plyometric Power'],
        'D3': ['Constrain to Afford', 'Repetition Without Repetition', 'Functional Variability'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Standard Rope'],
        'D7': ['Large 15m+'],
        'D8': ['Individual'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'game_keys': ['skipping_rope_sprint'],
    },
    'diamond-gates': {
        'D1': ['Dynamic Locomotor'],
        'D2': ['Change of Direction Speed', 'Reactive Agility', 'Horizontal Power'],
        'D3': ['Constrain to Potentiate', 'Attunement & Calibration', 'Self-Organisation', 'Functional Locomotion'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Small Group 3–5', 'Large Group 6+'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'game_keys': ['diamond_gates'],
    },
    'diamond-dribble': {
        'D1': ['Dynamic Locomotor'],
        'D2': ['Change of Direction Speed', 'Ball Manipulation / Dribbling', 'Reactive Agility'],
        'D3': ['Attunement & Calibration', 'Self-Organisation', 'Constrain to Potentiate'],
        'D4': ['Alternating'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Small Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Small Group 3–5', 'Large Group 6+'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'game_keys': ['diamond_dribble'],
    },
    'grid-leap-partner-feed': {
        'D1': ['Explosive & Landing'],
        'D2': ['Plyometric Power', 'Landing Mechanics', 'Hand-Eye Coordination'],
        'D3': ['Perception-Action Coupling', 'Self-Organisation', 'Interpersonal Coordination', 'Landscape of Affordances'],
        'D4': ['Bilateral', 'Unilateral'],
        'D6': ['Large Ball', 'Small Ball', 'Gate / Cone'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Pair'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'game_keys': ['leap_catching_throwing'],
    },
    'step-up-pairs': {
        'D1': ['Explosive & Landing'],
        'D2': ['Plyometric Power', 'Landing Mechanics', 'Bilateral Balance', 'Proprioception'],
        'D3': ['Perception-Action Coupling', 'Self-Organisation', 'Interpersonal Coordination'],
        'D4': ['Bilateral'],
        'D6': ['Large Ball', 'Small Ball', 'Step / Box'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Pair'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'game_keys': ['step_up'],
    },
    'grid-leap': {
        'D1': ['Explosive & Landing'],
        'D2': ['Plyometric Power', 'Landing Mechanics', 'Hand-Eye Coordination'],
        'D3': ['Perception-Action Coupling', 'Self-Organisation', 'Functional Variability', 'Constrain to Afford'],
        'D4': ['Bilateral', 'Unilateral'],
        'D5': ['Task'],
        'D6': ['Large Ball', 'Small Ball', 'Gate / Cone'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Individual'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'game_keys': ['leap_catching_throwing'],
    },
    'step-up': {
        'D1': ['Explosive & Landing'],
        'D2': ['Plyometric Power', 'Landing Mechanics', 'Bilateral Balance', 'Proprioception'],
        'D3': ['Perception-Action Coupling', 'Self-Organisation', 'Constrain to Afford'],
        'D4': ['Bilateral'],
        'D5': ['Task'],
        'D6': ['Large Ball', 'Small Ball', 'Step / Box', 'Wall'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Individual'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'game_keys': ['step_up'],
    },
    'balance-catch-pairs': {
        'D1': ['Balance & Postural Control'],
        'D2': ['Bilateral Balance', 'Unilateral Balance', 'Proprioception', 'Hand-Eye Coordination'],
        'D3': ['Perception-Action Coupling', 'Postural Attunement', 'Self-Organisation', 'Interpersonal Coordination'],
        'D4': ['Alternating'],
        'D6': ['Bosu / Balance Ball', 'Large Ball', 'Small Ball'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Pair'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'game_keys': ['balance_ball_catching'],
    },
    'diamond-gates-teams': {
        'D1': ['Dynamic Locomotor'],
        'D2': ['Change of Direction Speed', 'Reactive Agility', 'Hand-Eye Coordination'],
        'D3': ['Constrain to Potentiate', 'Perception-Action Coupling', 'Self-Organisation', 'Representative Task Design'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental', 'Interpersonal'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Medium 5–15m'],
        'D8': ['Small Group 3–5', 'Team 6+'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'game_keys': ['diamond_gates', 'diamond_dribble'],
    },
    'diamond-gates-team-dribbling': {
        'D1': ['Dynamic Locomotor', 'Perceptual-Motor Speed'],
        'D2': ['Ball Manipulation / Dribbling', 'Change of Direction Speed', 'Reactive Agility'],
        'D3': ['Attunement & Calibration', 'Self-Organisation', 'Constrain to Potentiate'],
        'D4': ['Alternating'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Small Group 3–5'],
        'D9': ['Level 1', 'Level 2'],
        'game_keys': ['diamond_dribble', 'diamond_gates'],
    },
    'ball-frog': {
        'D1': ['Explosive & Landing'],
        'D2': ['Plyometric Power', 'Landing Mechanics', 'Hand-Eye Coordination'],
        'D3': ['Perception-Action Coupling', 'Self-Organisation', 'Constrain to Afford', 'Functional Variability'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Small Ball'],
        'D7': ['Large 15m+'],
        'D8': ['Pair'],
        'D9': ['Level 2', 'Level 3'],
        'game_keys': ['leap_catching_throwing'],
    },
    'compass-ball': {
        'D1': ['Dynamic Locomotor', 'Perceptual-Motor Speed'],
        'D2': ['Reactive Agility', 'Change of Direction Speed', 'Hand-Eye Coordination', 'Foot-Eye Coordination'],
        'D3': ['Landscape of Affordances', 'Self-Organisation', 'Perception-Action Coupling'],
        'D4': ['Alternating'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Large Group 6+'],
        'D9': ['Level 2', 'Level 3'],
        'game_keys': ['diamond_gates'],
    },
    'zone-ranger': {
        'D1': ['Dynamic Locomotor', 'Perceptual-Motor Speed'],
        'D2': ['Reactive Agility', 'Change of Direction Speed', 'Foot-Eye Coordination'],
        'D3': ['Constrain to Afford', 'Representative Task Design', 'Perception-Action Coupling', 'Self-Organisation'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Small Group 3–5', 'Large Group 6+'],
        'D9': ['Level 2', 'Level 3'],
        'game_keys': ['diamond_gates'],
    },
    'out-of-the-kitchen': {
        'D1': ['Balance & Postural Control', 'Perceptual-Motor Speed'],
        'D2': ['Dynamic Balance', 'Bilateral Balance', 'Foot-Eye Coordination', 'Reactive Agility'],
        'D3': ['Perception-Action Coupling', 'Self-Organisation', 'Representative Task Design'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Net / Wall'],
        'D7': ['Medium 5–15m'],
        'D8': ['Small Group 3–5'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'game_keys': ['balance_ball_catching'],
    },
    'head-tennis': {
        'D1': ['Balance & Postural Control', 'Perceptual-Motor Speed'],
        'D2': ['Foot-Eye Coordination', 'Bilateral Balance', 'Reactive Agility', 'Proprioception'],
        'D3': ['Constrain to Afford', 'Self-Organisation', 'Perception-Action Coupling', 'Functional Variability'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Wall'],
        'D7': ['Medium 5–15m'],
        'D8': ['Pair', 'Small Group 3–5'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'game_keys': ['balance_ball_catching'],
    },
    'find-the-gap': {
        'D1': ['Dynamic Locomotor', 'Perceptual-Motor Speed'],
        'D2': ['Reactive Agility', 'Change of Direction Speed', 'Foot-Eye Coordination'],
        'D3': ['Constrain to Afford', 'Self-Organisation', 'Landscape of Affordances', 'Perception-Action Coupling'],
        'D4': ['Bilateral'],
        'D5': ['Environmental', 'Task'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Small Group 3–5', 'Large Group 6+'],
        'D9': ['Level 2', 'Level 3'],
        'game_keys': ['diamond_gates'],
    },
    'inside-running': {
        'D1': ['Dynamic Locomotor', 'Perceptual-Motor Speed'],
        'D2': ['Linear Speed', 'Ball Manipulation / Dribbling', 'Change of Direction Speed'],
        'D3': ['Perception-Action Coupling', 'Self-Organisation'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental', 'Interpersonal'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Pair', 'Large Group 6+'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'game_keys': ['diamond_dribble', 'diamond_gates'],
    },
    'street-gaelic-football': {
        'D1': ['Dynamic Locomotor', 'Perceptual-Motor Speed'],
        'D2': ['Foot-Eye Coordination', 'Hand-Eye Coordination', 'Reactive Agility', 'Change of Direction Speed'],
        'D3': ['Representative Task Design', 'Self-Organisation', 'Perception-Action Coupling'],
        'D4': ['Asymmetric'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Large Group 6+'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'game_keys': ['diamond_gates'],
    },
    'street-handball': {
        'D1': ['Dynamic Locomotor', 'Perceptual-Motor Speed'],
        'D2': ['Hand-Eye Coordination', 'Reactive Agility', 'Change of Direction Speed'],
        'D3': ['Representative Task Design', 'Self-Organisation', 'Perception-Action Coupling'],
        'D4': ['Asymmetric'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Medium 5–15m'],
        'D8': ['Large Group 6+'],
        'D9': ['Level 1', 'Level 2'],
        'game_keys': [],
    },
    'the-perfect-set': {
        'D1': ['Balance & Postural Control'],
        'D2': ['Foot-Eye Coordination', 'Bilateral Balance', 'Hand-Eye Coordination'],
        'D3': ['Constrain to Afford', 'Perception-Action Coupling', 'Self-Organisation', 'Representative Task Design'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Gate / Cone', 'Wall'],
        'D7': ['Medium 5–15m'],
        'D8': ['Pair'],
        'D9': ['Level 1', 'Level 2'],
        'game_keys': ['balance_ball_catching'],
    },
    'fast-4s': {
        'D1': ['Dynamic Locomotor', 'Perceptual-Motor Speed'],
        'D2': ['Change of Direction Speed', 'Linear Speed', 'Horizontal Power', 'Reactive Agility'],
        'D3': ['Constrain to Potentiate', 'Self-Organisation', 'Functional Locomotion', 'Perception-Action Coupling'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Large Group 6+'],
        'D9': ['Level 2', 'Level 3'],
        'game_keys': ['diamond_gates'],
    },
    'three-squared-programme': {
        'D1': ['Dynamic Locomotor'],
        'D2': ['Change of Direction Speed', 'Ball Manipulation / Dribbling', 'Reactive Agility'],
        'D3': ['Constrain to Afford', 'Attunement & Calibration', 'Self-Organisation', 'Functional Locomotion'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Adaptable'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'game_keys': ['diamond_gates', 'diamond_dribble'],
    },
    'split-decision': {
        'D1': ['Perceptual-Motor Speed', 'Explosive & Landing'],
        'D2': ['Reactive Agility', 'Change of Direction Speed', 'Landing Mechanics'],
        'D3': ['Perception-Action Coupling', 'Self-Organisation', 'Attunement & Calibration'],
        'D4': ['Bilateral'],
        'D6': ['Reflex Ball', 'Gate / Cone'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Pair', 'Small Group 3–5'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'game_keys': ['split_step'],
    },
    'split-step': {
        'D1': ['Perceptual-Motor Speed'],
        'D2': ['Reactive Agility', 'Change of Direction Speed'],
        'D3': ['Perception-Action Coupling', 'Attunement & Calibration', 'Self-Organisation'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Reflex Ball', 'Gate / Cone', 'Wall'],
        'D7': ['Moderate 5m×5m–10m×10m'],
        'D8': ['Individual'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'game_keys': ['split_step'],
    },
    'lateral-ladder': {
        'D1': ['Balance & Postural Control', 'Explosive & Landing'],
        'D2': ['Unilateral Balance', 'Plyometric Power', 'Landing Mechanics', 'Hand-Eye Coordination'],
        'D3': ['Perception-Action Coupling', 'Postural Attunement', 'Self-Organisation', 'Repetition Without Repetition'],
        'D4': ['Unilateral', 'Alternating'],
        'D5': ['Task'],
        'D6': ['Small Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Individual'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'game_keys': ['lateral_ladder'],
    },
    'lateral-ladder-partner-feed': {
        'D1': ['Balance & Postural Control', 'Explosive & Landing'],
        'D2': ['Unilateral Balance', 'Plyometric Power', 'Landing Mechanics', 'Hand-Eye Coordination'],
        'D3': ['Perception-Action Coupling', 'Postural Attunement', 'Self-Organisation', 'Interpersonal Coordination'],
        'D4': ['Unilateral', 'Alternating'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Small Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Pair'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'game_keys': ['lateral_ladder'],
    },
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
        "L1 — 50 cm dots · 12 squares · target: 6 claimed",
        "L2 — 50 cm dots · 15 squares · target: 9 claimed",
        "L3 — 50 cm dots · 15 squares · target: all 15 claimed",
        "L4 — 60 cm dots · 15 squares · target: 9 claimed",
        "L5 — 75 cm dots · 15 squares · target: 12 claimed",
    ],
    "lateral_ladder": [
        "L1 — 0.5 m rung spacing · 6 m course · target: 10 dots claimed",
        "L2 — 0.5 m rung spacing · 6 m course · target: 18 dots claimed",
        "L3 — 0.75 m rung spacing · 9 m course · target: 16 dots claimed",
        "L4 — 1.0 m rung spacing · 12 m course · target: 16 dots claimed",
        "L5 — 1.25 m rung spacing · 15 m course · target: 20 dots claimed",
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
    {
        "display_name": "Lateral Ladder",
        "game_key":     "lateral_ladder",
        "field_key":    "dots_claimed",
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
        "cla_constraint": (
            "The key constraint here is a dual-task balance demand — the athlete must maintain "
            "a stable postural base while simultaneously processing and responding to an "
            "incoming stimulus. Game environments that pair a balance requirement with "
            "a perceptual demand (catching, tracking, reacting) will directly challenge this."
        ),
        "resource_tag": "balance",
        "sc_gap": (
            "Bilateral balance deficit — the proprioceptive system is not adequately "
            "managing postural stability under a dual-task demand (balance + catch). "
            "The stable base required to support a secondary perceptual demand is not yet established."
        ),
        "sc_programme": (
            "Bilateral proprioceptive loading: single-plane balance holds progressing to unstable "
            "surfaces. Wall-supported catching as a controlled dual-task. Calf and ankle stability "
            "work underpins the postural hold."
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
        "cla_constraint": (
            "The constraint here is unilateral balance under perceptual load — managing a "
            "single-leg base while tracking and intercepting a moving object. Game environments "
            "that require single-leg stability alongside a perceptual or manipulation task "
            "will expose and develop this coupling."
        ),
        "resource_tag": "balance",
        "sc_gap": (
            "Unilateral balance deficit — single-leg proprioceptive control is insufficient "
            "to support a secondary perceptual demand. The athlete cannot yet stabilise on "
            "one foot while simultaneously tracking and catching a ball."
        ),
        "sc_programme": (
            "Unilateral proprioceptive control progressively: single-leg holds → single-leg "
            "with arm reach → single-leg catch. Only introduce unstable surfaces once stable "
            "ground control is consistent. Hip abductor and ankle stability work (single-leg "
            "deadlifts, lateral band walks) directly supports this area."
        ),
        "d2_focus": ["Unilateral balance", "Proprioception", "Perceptual-action coupling"],
        "athlete_what": "Balancing on one leg while tracking a ball is a real skill — and it's very trainable.",
        "athlete_why": "Most sport happens on one leg — cutting, landing, holding your position. Getting comfortable here makes you more robust and harder to knock off balance.",
        "athlete_games": ["Balance Ball Catching (self-test)", "Step Up", "Grid Leap"],
        "athlete_sc": "Practice standing on one leg for 30 seconds at a time — once that's easy, try catching a ball while you do it. Simple but effective.",
    },
    ("lateral_ladder", "dots_claimed"): {
        "display": "Lateral Ladder",
        "family": "Balance & Postural Control",
        "cla_constraint": (
            "The constraint here is lateral projective movement with concurrent ball handling "
            "— the athlete must couple an explosive skater leap with a self-lob throw and catch, "
            "all while landing accurately on a defined target. Game environments that combine "
            "lateral displacement, landing accuracy, and a perceptual task (tracking, catching) "
            "will directly challenge and develop this coupling."
        ),
        "resource_tag": "balance",
        "sc_gap": (
            "Lateral power and landing mechanics deficit — the athlete is unable to generate "
            "and absorb explosive lateral movement while simultaneously managing a perceptual "
            "task. Single-leg lateral control and lateral plyometric loading are underdeveloped."
        ),
        "sc_programme": (
            "Lateral plyometric progression: lateral box steps → lateral hops to stick → "
            "reactive lateral bounds. Single-leg lateral band work (hip abductors) to support "
            "landing control. Pair with simple catch tasks once landing control is established."
        ),
        "d2_focus": ["Unilateral balance", "Lateral power", "Hand-eye coordination"],
        "athlete_what": "Your lateral leaping power and landing control is an area to build — it's a very coachable movement quality.",
        "athlete_why": "Explosive lateral movement — cutting, closing gaps, getting to a ball wide — is one of the most important physical qualities in sport. Landing well on those movements keeps you injury-free.",
        "athlete_games": ["Lateral Ladder (self-test)", "Lob Scotch", "Grid Leap"],
        "athlete_sc": "Stand side-on and practice lateral hops, landing on one foot and holding for 2 seconds before hopping back. Keep your knee soft and land quietly.",
    },
    ("lob_scotch", "squares_scored"): {
        "display": "Lob Scotch",
        "family": "Explosive & Landing",
        "cla_constraint": (
            "The constraint here is projective movement with temporal and spatial precision "
            "— the athlete must hop, land in a defined zone, and rebalance within a rhythmic "
            "structure. Game environments with target-based landing, hop-and-recover patterns, "
            "or scoring zones that reward landing accuracy will develop this."
        ),
        "resource_tag": "explosive",
        "sc_gap": (
            "Dynamic landing mechanics deficit — inadequate bilateral landing control "
            "following a unilateral projective movement. Landing absorption and re-stabilisation "
            "from the hop-to-land transition is underdeveloped."
        ),
        "sc_programme": (
            "Progressive landing mechanics: drop landings → box step-offs → unilateral hops "
            "to bilateral landing. Cue knee-over-toe alignment and full ankle dorsiflexion "
            "on contact. Eccentric quad and glute strength underpins the absorption capacity."
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
        "cla_constraint": (
            "The constraint here is horizontal projection with concurrent ball interception "
            "— the athlete must couple explosive force output with visual tracking and spatial "
            "targeting simultaneously. Look for games that require leaping to intercept, "
            "or that score for both distance and accuracy in the same action."
        ),
        "resource_tag": "explosive",
        "sc_gap": (
            "Horizontal power and spatial targeting deficit — inadequate projective force "
            "production and/or landing accuracy under a concurrent perceptual demand. "
            "The athlete cannot yet couple horizontal force output with simultaneous ball "
            "tracking and spatial target awareness."
        ),
        "sc_programme": (
            "Horizontal power with landing accuracy together: broad jumps to a target zone, "
            "medicine ball horizontal throws for force production. Reactive catch-and-jump "
            "sequences. Accuracy and distance should develop in parallel, not in series."
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
        "cla_constraint": (
            "The constraint here is rhythmic locomotion under a dual-task demand — the athlete "
            "must sustain a movement rhythm while simultaneously tracking and intercepting an "
            "object. Games that impose a locomotor rhythm alongside a perceptual task (catching, "
            "receiving, scanning) will create the right environment for this to develop."
        ),
        "resource_tag": "explosive",
        "sc_gap": (
            "Vertical force production with concurrent hand-eye coordination deficit — "
            "step-up rhythm and catch timing are decoupled. The athlete cannot yet maintain "
            "the full perception-action loop through the complete vertical movement cycle."
        ),
        "sc_programme": (
            "Build step-up rhythm before adding the ball: metronome-paced step-ups focusing "
            "on full hip extension at the top. Once rhythm is consistent, introduce the "
            "self-feed wall catch. Vertical power foundation work (box step-ups, loaded "
            "step-ups, calf raises) reduces cognitive load on the movement pattern."
        ),
        "d2_focus": ["Vertical power", "Rhythmic coordination", "Perceptual-action coupling"],
        "athlete_what": "Keeping your rhythm while doing two things at once — stepping and catching — is a great skill to build.",
        "athlete_why": "Athletes who can keep moving consistently while tracking a ball have a real edge. This tests whether your body can run on autopilot so your mind can focus on the game.",
        "athlete_games": ["Step Up (self-test)", "Skipping Rope Sprint", "Diamond Gates"],
        "athlete_sc": "Box step-ups directly support this — focus on driving all the way up to a full hip extension at the top.",
    },
    ("skipping_rope_sprint", "average"): {
        "display": "Skipping Rope Sprints",
        "family": "Dynamic Locomotor",
        "cla_constraint": (
            "The constraint here is linear speed under a self-imposed coordination demand "
            "— the rope adds a rhythmic, continuous constraint that the athlete must synchronise "
            "with their locomotion. Games with continuous movement rhythms, repetitive patterns, "
            "or constraints that require coordination to be maintained at speed will develop this."
        ),
        "resource_tag": "locomotion",
        "sc_gap": (
            "Linear speed with rhythmic coordination deficit — the athlete cannot yet "
            "synchronise locomotion with rope rotation at sufficient pace. Sprint mechanics "
            "and rope timing are not coupled, reducing the efficiency of the locomotor pattern."
        ),
        "sc_programme": (
            "Acceleration work (wall drives, A-skips, resisted sprint starts) builds the "
            "speed foundation. Progress to combined rope-sprint sets once each element is "
            "consistent in isolation. Note: lower time is better for this metric."
        ),
        "d2_focus": ["Linear speed", "Rhythmic coordination"],
        "athlete_what": "Your running speed and coordination under a constraint is something to develop — and it responds really well to practice.",
        "athlete_why": "Pure speed is one of the most valuable things in sport. Getting faster over short distances — and staying coordinated while you do it — is a game-changer.",
        "athlete_games": ["Skipping Rope Sprint (self-test)", "Diamond Gates", "Diamond Dribble"],
        "athlete_sc": "Acceleration drills: wall drive holds, A-skips, short sprint starts from standing. Focus on the first 5 metres.",
    },
    ("diamond_gates", "small_group"): {
        "display": "Diamond Gates",
        "family": "Dynamic Locomotor",
        "cla_constraint": (
            "The constraint here is multi-directional movement under spatial and time pressure "
            "— the gates define the path but the athlete must self-organise their route, "
            "deceleration, and re-acceleration within a group context. Games with defined "
            "movement zones, gate structures, or scoring that rewards agility and efficiency "
            "will challenge this directly."
        ),
        "resource_tag": "agility",
        "sc_gap": (
            "Change of direction speed deficit — the athlete is not efficiently navigating "
            "the spatial structure of the diamond under the group time constraint. "
            "Deceleration mechanics, re-acceleration, and turning efficiency need development."
        ),
        "sc_programme": (
            "COD speed: deceleration mechanics first (hip-sink, foot-strike positioning), "
            "then 5-10-5 shuttle progressions, lateral shuffle to sprint transitions. "
            "Rear-foot-elevated split squats and lateral band work for hip abductor control "
            "in the change-of-direction moment."
        ),
        "d2_focus": ["Change of direction speed", "Reactive agility"],
        "athlete_what": "Changing direction quickly and efficiently is something to keep working on — this is one of the most impactful areas in field and court sports.",
        "athlete_why": "The ability to stop, change direction and accelerate again quickly is at the heart of getting to the right place before anyone else.",
        "athlete_games": ["Diamond Gates (self-test & programme)", "Diamond Dribble", "Split Step"],
        "athlete_sc": "Shuttle runs — short, sharp, and frequent. Focus on the deceleration (the slow-down before you turn) as much as the sprint.",
    },
    ("diamond_dribble", "small_group"): {
        "display": "Diamond Dribble",
        "family": "Dynamic Locomotor",
        "cla_constraint": (
            "The constraint here is ball-locomotor coupling under spatial and time pressure "
            "— the dribble adds a concurrent manipulation demand that competes for attentional "
            "resources with movement quality. Games that require moving with an object through "
            "defined space, or that reward fluid ball movement alongside agility, will develop "
            "this coupling."
        ),
        "resource_tag": "agility",
        "sc_gap": (
            "Change of direction speed with concurrent ball manipulation deficit — "
            "the dribble constraint is absorbing perceptual and motor resources, "
            "reducing locomotor efficiency. Dual-task capacity (movement quality + "
            "ball control) is underdeveloped."
        ),
        "sc_programme": (
            "Address movement quality as the priority: COD mechanics, deceleration control, "
            "and unilateral leg strength (split squats, lateral lunges). Ball manipulation "
            "develops separately — combine only once the movement pattern is sufficiently "
            "automatic that it no longer competes for attentional resources."
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
        "cla_constraint": (
            "The constraint here is reactive interception under temporal uncertainty — the "
            "athlete must respond to an unpredictable stimulus with minimal preparation time. "
            "Ensure this athlete gets exposure to games with genuine unpredictability: partner "
            "reaction tasks, chaotic environments, or games where they cannot anticipate the "
            "next stimulus. Choreographed patterns will not develop this."
        ),
        "resource_tag": "reaction",
        "sc_gap": (
            "Reactive agility deficit — the athlete is not intercepting the reflex ball "
            "within the available temporal window at sufficient rate. Reactive speed and "
            "the coupling between visual stimulus and motor response are limiting performance."
        ),
        "sc_programme": (
            "Reactive agility: visual stimulus to movement response drills, 1v1 mirroring, "
            "partner signal COD. Drop-catch drills and rapid ground contact (pogo) work reduce "
            "ground contact time. Critically: S&C adaptation must occur under genuine "
            "unpredictability to transfer — avoid choreographed agility patterns."
        ),
        "d2_focus": ["Reactive agility", "Perceptual-action coupling"],
        "athlete_what": "Reacting quickly to a ball that you can't predict is something to sharpen — this is one of the most sport-specific skills there is.",
        "athlete_why": "The best athletes read play early and move before anyone else. This test measures exactly that — your ability to pick up cues and react instantly.",
        "athlete_games": ["Split Step (self-test)", "Split Decision", "Diamond Gates"],
        "athlete_sc": "Reaction games with a partner — they point, you move. Or drop-catch drills: hold a ball at shoulder height, drop it, catch before it bounces twice.",
    },
}
