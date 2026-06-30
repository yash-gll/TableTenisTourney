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
# Saturation constant for play-derived skills (higher = slower climb).
DERIVATION_K = 15

# Faults: a point lost to an unforced error. Each gifts the rally to the
# opponent AND counts *against* the named skill for the player who committed it.
# (key, display label, mapped skill)
FAULTS: list[tuple[str, str, str]] = [
    ("wrong_serve", "Wrong serve", "serve"),
    ("serve_net", "Serve into net", "serve"),
    ("serve_out", "Serve long / out", "serve"),
    ("hit_net", "Hit into net", "consistency"),
    ("hit_out", "Hit out / long", "consistency"),
    ("out_of_position", "Out of position", "footwork"),
]
FAULT_KEYS: set[str] = {key for key, _, _ in FAULTS}
FAULT_SKILL: dict[str, str] = {key: skill for key, _, skill in FAULTS}


def default_ratings() -> dict[str, int]:
    return {key: DEFAULT_SKILL for key, _ in SKILL_ATTRIBUTES}


def derived_skill(wins: int, errors: int = 0) -> int:
    """Map a player's net points (wins minus faults) for a skill to a 0–100 rating.

    Baseline 50; winning rallies with the skill push toward 100, faults pull
    toward 0, both with diminishing returns. Symmetric around the baseline, so a
    clean record (errors=0) reduces to the old winners-only curve."""
    net = wins - errors
    raw = DEFAULT_SKILL + (100 - DEFAULT_SKILL) * net / (abs(net) + DERIVATION_K)
    return max(SKILL_MIN, min(SKILL_MAX, round(raw)))


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
