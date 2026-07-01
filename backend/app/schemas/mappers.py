"""Helpers that build response schemas from joined User + PlayerProfile models."""

from app.db.models.match import Match
from app.db.models.player_profile import PlayerProfile
from app.db.models.team import Team
from app.db.models.tournament import Tournament
from app.db.models.user import User
from app.domain import tournament_state
from app.schemas.admin import AdminPlayerOut
from app.schemas.match import MatchOut
from app.schemas.player import MeResponse, PlayerProfileOut
from app.schemas.team import TeamMemberOut, TeamOut
from app.schemas.tournament import TournamentOut


def to_me(user: User) -> MeResponse:
    profile = user.profile
    return MeResponse(
        user_id=user.id,
        email=user.email,
        role=user.role,
        account_status=user.account_status,
        email_verified=user.is_verified,
        approval_status=profile.approval_status,
        display_name=profile.display_name,
    )


def to_profile_out(user: User) -> PlayerProfileOut:
    profile = user.profile
    return PlayerProfileOut(
        id=profile.id,
        user_id=user.id,
        display_name=profile.display_name,
        email=user.email,
        role=user.role,
        account_status=user.account_status,
        approval_status=profile.approval_status,
        approval_reason=profile.approval_reason,
        current_rating=profile.current_rating,
        highest_rating=profile.highest_rating,
        bio=profile.bio,
        skill_ratings=profile.skill_ratings or {},
        email_verified=user.is_verified,
        created_at=user.created_at,
    )


def to_tournament_out(t: Tournament) -> TournamentOut:
    return TournamentOut(
        id=t.id,
        name=t.name,
        slug=t.slug,
        description=t.description,
        location=t.location,
        start_at=t.start_at,
        end_at=t.end_at,
        status=t.status,
        visibility=t.visibility,
        target_points=t.target_points,
        win_by_two=t.win_by_two,
        maximum_points=t.maximum_points,
        win_table_points=t.win_table_points,
        loss_table_points=t.loss_table_points,
        version=t.version,
        team_count=len(t.teams),
        is_editable=tournament_state.is_editable(t.status),
        created_at=t.created_at,
    )


def to_team_out(team: Team) -> TeamOut:
    members = [
        TeamMemberOut(
            player_id=m.player_id,
            display_name=m.player.display_name,
            current_rating=m.player.current_rating,
            member_order=m.member_order,
        )
        for m in team.members
    ]
    avg = (
        round(sum(m.current_rating for m in members) / len(members), 1) if members else None
    )
    return TeamOut(
        id=team.id,
        tournament_id=team.tournament_id,
        name=team.name,
        logo_url=team.logo_url,
        initial_seed=team.initial_seed,
        members=members,
        average_rating=avg,
        is_complete=len(members) == 2,
    )


def to_match_out(match: Match) -> MatchOut:
    return MatchOut(
        id=match.id,
        tournament_id=match.tournament_id,
        stage=match.stage,
        round_number=match.round_number,
        display_order=match.display_order,
        court_name=match.court_name,
        team_a_id=match.team_a_id,
        team_b_id=match.team_b_id,
        team_a_name=match.team_a.name if match.team_a else None,
        team_b_name=match.team_b.name if match.team_b else None,
        team_a_score=match.team_a_score,
        team_b_score=match.team_b_score,
        winner_team_id=match.winner_team_id,
        loser_team_id=match.loser_team_id,
        status=match.status,
        scheduled_at=match.scheduled_at,
        started_at=match.started_at,
        completed_at=match.completed_at,
        version=match.version,
        serve_pairing=match.serve_pairing,
        first_server_id=match.first_server_id,
    )


def to_admin_player_out(profile: PlayerProfile) -> AdminPlayerOut:
    user = profile.user
    return AdminPlayerOut(
        player_id=profile.id,
        user_id=profile.user_id,
        display_name=profile.display_name,
        email=user.email,
        approval_status=profile.approval_status,
        approval_reason=profile.approval_reason,
        email_verified=user.is_verified,
        created_at=profile.created_at,
    )
