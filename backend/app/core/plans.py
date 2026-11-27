"""Central subscription plan configuration (backend master spec, section 5
and 54: prices and quotas live here ONLY — never duplicated in frontend
components or scattered across backend files).
"""

from dataclasses import dataclass

from app.models.subscription import SubscriptionPlan


@dataclass(frozen=True)
class PlanConfig:
    stars_price: int
    duration_days: int
    call_minutes_per_day: int


SUBSCRIPTION_PLANS: dict[SubscriptionPlan, PlanConfig] = {
    SubscriptionPlan.DAILY: PlanConfig(stars_price=150, duration_days=1, call_minutes_per_day=15),
    SubscriptionPlan.WEEKLY: PlanConfig(stars_price=300, duration_days=7, call_minutes_per_day=45),
    SubscriptionPlan.MONTHLY: PlanConfig(stars_price=400, duration_days=30, call_minutes_per_day=90),
    SubscriptionPlan.YEARLY: PlanConfig(stars_price=3800, duration_days=365, call_minutes_per_day=300),
}

# Free vs Premium limits (spec section 6/8/14) — also centralized here so
# limit_service.py and messages don't hardcode numbers independently.
FREE_DAILY_LIKE_LIMIT = 20
PREMIUM_DAILY_LIKE_LIMIT = 100
FREE_MESSAGES_PER_NEW_CONTACT = 2
PREMIUM_DAILY_MESSAGE_LIMIT = 100
PREMIUM_DAILY_PHOTO_LIMIT = 10

# VIP capacity — raised from 100 to 500 per owner's request.
VIP_CAPACITY = 500

# Free plan gets no call minutes by default — calling is a Premium feature.
# Free users can still unlock temporary minutes by watching a rewarded ad.
FREE_DAILY_CALL_MINUTES = 0

# Rewarded ads (offerwall, e.g. AdMantum) — one verified ad view grants:
AD_REWARD_BONUS_MESSAGES = 3      # extra messages for that one conversation
AD_REWARD_BONUS_CALL_MINUTES = 10  # extra call minutes for today
# A pending ad session not confirmed by provider postback within this
# window is considered abandoned/fraudulent and expires.
AD_REWARD_SESSION_TTL_SECONDS = 10 * 60
