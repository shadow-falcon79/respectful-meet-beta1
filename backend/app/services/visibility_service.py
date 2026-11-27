"""Feed ranking (backend master spec section 13/45-49). Free users always
stay discoverable — Premium gets a priority boost, never an absolute
guarantee, and never removes Free profiles from the pool.
"""

from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.services.subscription_service import is_premium

PROFILE_COMPLETION_FIELDS = ("bio", "interests")


def _completion_score(profile: Profile) -> float:
    filled = 0
    if profile.bio:
        filled += 1
    if profile.interests:
        filled += 1
    return filled / len(PROFILE_COMPLETION_FIELDS)


def rank_profiles(db: Session, profiles: list[Profile]) -> list[Profile]:
    """Sorts profiles by a simple composite score: profile completion +
    recency (as an activity proxy for now — real "last active" tracking
    isn't wired up yet) + a Premium boost. No factor is ever large enough
    to fully hide a Free profile behind Premium ones."""

    def score(profile: Profile) -> tuple[float, float]:
        completion = _completion_score(profile)
        premium_boost = 0.15 if is_premium(db, profile.user_id) else 0.0
        # created_at as a stand-in "recency" signal until real activity
        # tracking (last_active_at) exists.
        recency = profile.created_at.timestamp()
        return (completion + premium_boost, recency)

    return sorted(profiles, key=score, reverse=True)
