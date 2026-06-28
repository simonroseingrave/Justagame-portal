"""Shared constants for the Just A Game Activity & Achievement Portal."""

# The four development pillars used across Just A Game's coaching philosophy
# (constraints-led / athlete adaptability approach).
CATEGORIES = [
    "Physical Capability",
    "Game Understanding",
    "Skill Adaptability",
    "Confidence & Resilience",
]

CATEGORY_BLURBS = {
    "Physical Capability": "Athletic movement, conditioning and physical foundations.",
    "Game Understanding": "Decision-making, game-reading and tactical awareness.",
    "Skill Adaptability": "Adapting technique and skills to dynamic, game-like situations.",
    "Confidence & Resilience": "Confidence, resilience and personal growth.",
}

CATEGORY_ICONS = {
    "Physical Capability": "\U0001F3C3",       # runner
    "Game Understanding": "\U0001F9E0",        # brain
    "Skill Adaptability": "\U0001F504",        # adapt/refresh
    "Confidence & Resilience": "\U0001F525",   # fire
}

SPORTS = ["Cricket", "Football", "Hockey", "Multi-sport"]

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
