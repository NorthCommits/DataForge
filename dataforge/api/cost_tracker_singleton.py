from __future__ import annotations

from .cost_tracker import CostTracker
from ..config import get_settings

_cost_tracker: CostTracker | None = None


def get_cost_tracker() -> CostTracker:
    global _cost_tracker
    if _cost_tracker is None:
        settings = get_settings()
        _cost_tracker = CostTracker(
            daily_budget_usd=settings.api.cost_limits.daily_budget,
            alert_threshold_usd=settings.api.cost_limits.alert_threshold,
        )
    return _cost_tracker
