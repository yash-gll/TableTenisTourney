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
  email_verified: boolean;
  created_at: string;
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
