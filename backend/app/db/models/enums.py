import enum


class UserRole(str, enum.Enum):
    PLAYER = "PLAYER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class AccountStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DISABLED = "DISABLED"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class AuthTokenType(str, enum.Enum):
    EMAIL_VERIFY = "EMAIL_VERIFY"
    PASSWORD_RESET = "PASSWORD_RESET"


class AuditSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class TournamentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    REGISTRATION_OPEN = "REGISTRATION_OPEN"
    REGISTRATION_CLOSED = "REGISTRATION_CLOSED"
    SCHEDULED = "SCHEDULED"
    GROUP_IN_PROGRESS = "GROUP_IN_PROGRESS"
    GROUP_COMPLETE = "GROUP_COMPLETE"
    QUALIFIERS_IN_PROGRESS = "QUALIFIERS_IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FINALIZED = "FINALIZED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


class TournamentVisibility(str, enum.Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    UNLISTED = "UNLISTED"


class MatchStatus(str, enum.Enum):
    WAITING_FOR_TEAMS = "WAITING_FOR_TEAMS"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    VOID = "VOID"


class MatchStage(str, enum.Enum):
    GROUP = "GROUP"
    QF1 = "QF1"
    QF2 = "QF2"
    QF3 = "QF3"
    FINAL = "FINAL"
    TIEBREAKER = "TIEBREAKER"


class DependencySlot(str, enum.Enum):
    TEAM_A = "TEAM_A"
    TEAM_B = "TEAM_B"


class DependencyOutcome(str, enum.Enum):
    WINNER = "WINNER"
    LOSER = "LOSER"


class RatingEventType(str, enum.Enum):
    MATCH_RESULT = "MATCH_RESULT"
    MATCH_CORRECTION_REVERSAL = "MATCH_CORRECTION_REVERSAL"
    MATCH_CORRECTION_REAPPLY = "MATCH_CORRECTION_REAPPLY"
    TOURNAMENT_PLACEMENT_BONUS = "TOURNAMENT_PLACEMENT_BONUS"
    ADMIN_ADJUSTMENT = "ADMIN_ADJUSTMENT"
    SEASON_RESET = "SEASON_RESET"


class SnapshotType(str, enum.Enum):
    TOURNAMENT_START = "TOURNAMENT_START"
    TOURNAMENT_END = "TOURNAMENT_END"


class RegistrationStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    WAITLISTED = "WAITLISTED"
    DECLINED = "DECLINED"
    WITHDRAWN = "WITHDRAWN"
