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
