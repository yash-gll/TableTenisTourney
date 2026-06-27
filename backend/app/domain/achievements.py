"""Pure achievement/badge rules — derived from a player's aggregate stats."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Badge:
    key: str
    label: str
    icon: str
    description: str


@dataclass(frozen=True)
class AchievementInput:
    titles: int            # tournaments won (champion)
    finals_reached: int    # champion or runner-up
    podiums: int           # top-4 finishes
    matches_played: int
    wins: int
    longest_win_streak: int


def earned_badges(s: AchievementInput) -> list[Badge]:
    badges: list[Badge] = []

    if s.titles >= 3:
        badges.append(Badge("dynasty", "Dynasty", "👑", f"Won {s.titles} tournaments"))
    elif s.titles >= 1:
        badges.append(Badge("champion", "Champion", "🏆", "Won a tournament"))

    if s.finals_reached >= 1 and s.titles == 0:
        badges.append(Badge("finalist", "Finalist", "🥈", "Reached a tournament final"))

    if s.podiums >= 1 and s.finals_reached == 0:
        badges.append(Badge("podium", "Podium", "🥉", "Finished top 4 in a tournament"))

    if s.longest_win_streak >= 5:
        badges.append(Badge("unstoppable", "Unstoppable", "🔥", f"{s.longest_win_streak}-match win streak"))
    elif s.longest_win_streak >= 3:
        badges.append(Badge("on_fire", "On Fire", "🔥", "Won 3 matches in a row"))

    if s.matches_played >= 10:
        win_pct = round(s.wins / s.matches_played * 100)
        if win_pct >= 60:
            badges.append(Badge("sharpshooter", "Sharpshooter", "🎯", f"{win_pct}% win rate"))

    if s.matches_played >= 50:
        badges.append(Badge("veteran", "Veteran", "🎾", "Played 50+ matches"))
    elif s.matches_played >= 10:
        badges.append(Badge("regular", "Regular", "🏓", "Played 10+ matches"))

    return badges
