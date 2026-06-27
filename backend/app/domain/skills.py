"""Player skill attributes (admin-curated, 0-100).

Distinct from the competitive Elo rating: skills are a coaching-style profile
set by admins, not earned from matches. Edit this list to add/remove attributes
(values live in a JSONB column, so no migration is needed to change the set).
"""

# (key, display label)
SKILL_ATTRIBUTES: list[tuple[str, str]] = [
    ("serve", "Serve"),
    ("smash", "Smash"),
    ("spin", "Spin"),
    ("footwork", "Footwork"),
    ("consistency", "Consistency"),
]

SKILL_KEYS: set[str] = {key for key, _ in SKILL_ATTRIBUTES}
SKILL_MIN = 0
SKILL_MAX = 100
# Baseline assigned when a player is approved; admins tune from here.
DEFAULT_SKILL = 50


def default_ratings() -> dict[str, int]:
    return {key: DEFAULT_SKILL for key, _ in SKILL_ATTRIBUTES}


def labelled(stored: dict | None) -> list[dict]:
    """Return the canonical ordered list with each attribute's stored value (or None)."""
    stored = stored or {}
    return [{"key": key, "label": label, "value": stored.get(key)} for key, label in SKILL_ATTRIBUTES]


def validate_ratings(ratings: dict[str, int]) -> tuple[bool, str | None]:
    for key, value in ratings.items():
        if key not in SKILL_KEYS:
            return False, f"Unknown skill '{key}'."
        if not isinstance(value, int) or value < SKILL_MIN or value > SKILL_MAX:
            return False, f"'{key}' must be an integer between {SKILL_MIN} and {SKILL_MAX}."
    return True, None
