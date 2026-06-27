export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED" | "SUSPENDED";
export type AccountStatus = "ACTIVE" | "SUSPENDED" | "DISABLED";
export type UserRole = "PLAYER" | "ADMIN" | "SUPER_ADMIN";

export interface Me {
  user_id: string;
  email: string;
  role: UserRole;
  account_status: AccountStatus;
  email_verified: boolean;
  approval_status: ApprovalStatus;
  display_name: string;
}

export interface PlayerProfile {
  id: string;
  user_id: string;
  display_name: string;
  email: string;
  role: UserRole;
  account_status: AccountStatus;
  approval_status: ApprovalStatus;
  approval_reason: string | null;
  current_rating: number;
  highest_rating: number;
  bio: string | null;
  skill_ratings: Record<string, number>;
  email_verified: boolean;
  created_at: string;
}

export interface SkillItem {
  key: string;
  label: string;
  value: number | null;
}

export interface PlayerSkills {
  player_id: string;
  display_name: string;
  skills: SkillItem[];
}

export interface PublicPlayer {
  player_id: string;
  display_name: string;
  current_rating: number;
  highest_rating: number;
}

export interface PlayerStats {
  matches_played: number;
  wins: number;
  losses: number;
  win_pct: number;
  tournaments_played: number;
  tournament_wins: number;
}

export interface PublicProfile {
  player_id: string;
  display_name: string;
  current_rating: number;
  highest_rating: number;
  stats: PlayerStats;
  recent_form: string[];
}

export interface Rival {
  opponent_id: string;
  opponent_name: string;
  meetings: number;
  wins: number;
  losses: number;
}

export interface PlayerRivals {
  player_id: string;
  rivals: Rival[];
}

export interface Badge {
  key: string;
  label: string;
  icon: string;
  description: string;
}

export interface PlayerAchievements {
  player_id: string;
  achievements: Badge[];
}

export type RegistrationStatus =
  | "REQUESTED"
  | "ACCEPTED"
  | "WAITLISTED"
  | "DECLINED"
  | "WITHDRAWN";

export interface MyRegistration {
  status: RegistrationStatus | null;
}

export interface RegistrationItem {
  player_id: string;
  display_name: string;
  status: RegistrationStatus;
  preferred_partner_id: string | null;
  note: string | null;
  created_at: string;
}

export interface MyPrediction {
  match_id: string;
  predicted_winner_team_id: string;
  is_correct: boolean | null;
}

export interface PredictionRow {
  player_id: string;
  display_name: string;
  points: number;
  correct: number;
  total: number;
}

export interface AdminPlayer {
  player_id: string;
  user_id: string;
  display_name: string;
  email: string;
  approval_status: ApprovalStatus;
  approval_reason: string | null;
  email_verified: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export type TournamentStatus =
  | "DRAFT"
  | "REGISTRATION_OPEN"
  | "REGISTRATION_CLOSED"
  | "SCHEDULED"
  | "GROUP_IN_PROGRESS"
  | "GROUP_COMPLETE"
  | "QUALIFIERS_IN_PROGRESS"
  | "COMPLETED"
  | "FINALIZED"
  | "PAUSED"
  | "CANCELLED"
  | "ARCHIVED";

export type Visibility = "PUBLIC" | "PRIVATE" | "UNLISTED";

export interface Tournament {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  location: string | null;
  start_at: string | null;
  end_at: string | null;
  status: TournamentStatus;
  visibility: Visibility;
  target_points: number;
  win_by_two: boolean;
  maximum_points: number | null;
  win_table_points: number;
  loss_table_points: number;
  version: number;
  team_count: number;
  is_editable: boolean;
  created_at: string;
}

export interface TeamMember {
  player_id: string;
  display_name: string;
  current_rating: number;
  member_order: number;
}

export interface Team {
  id: string;
  tournament_id: string;
  name: string;
  logo_url: string | null;
  initial_seed: number | null;
  members: TeamMember[];
  average_rating: number | null;
  is_complete: boolean;
}

export type MatchStatus =
  | "WAITING_FOR_TEAMS"
  | "SCHEDULED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "CANCELLED"
  | "VOID";

export type MatchStage = "GROUP" | "QF1" | "QF2" | "QF3" | "FINAL" | "TIEBREAKER";

export interface Match {
  id: string;
  tournament_id: string;
  stage: MatchStage;
  round_number: number | null;
  display_order: number | null;
  court_name: string | null;
  team_a_id: string | null;
  team_b_id: string | null;
  team_a_name: string | null;
  team_b_name: string | null;
  team_a_score: number | null;
  team_b_score: number | null;
  winner_team_id: string | null;
  loser_team_id: string | null;
  status: MatchStatus;
  scheduled_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  version: number;
}

export interface Standing {
  rank: number;
  team_id: string;
  team_name: string;
  played: number;
  wins: number;
  losses: number;
  table_points: number;
  points_for: number;
  points_against: number;
  point_difference: number;
  tie_status: string;
  qualification_status: string;
}

export interface Leaderboard {
  group_complete: boolean;
  standings: Standing[];
}

export interface ExplanationResponse {
  explanation: string[];
}

export interface Placement {
  place: number;
  team_id: string;
  team_name: string;
}

export interface Bracket {
  matches: Match[];
  placements: Placement[];
}

export interface RatingEvent {
  id: string;
  tournament_id: string | null;
  match_id: string | null;
  event_type: string;
  rating_before: number;
  delta: number;
  rating_after: number;
  reason: string | null;
  created_at: string;
}

export interface HistoryItem {
  id: string;
  name: string;
  slug: string;
  location: string | null;
  finalized_at: string | null;
  champion_team_id: string | null;
  champion_name: string | null;
}

export interface HistoryDetail {
  id: string;
  name: string;
  location: string | null;
  status: string;
  finalized_at: string | null;
  champion_name: string | null;
  placements: Placement[];
}
