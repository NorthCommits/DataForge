from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class CostBreakdown:
    tavily_usd: float = 0.0
    openai_usd: float = 0.0

    @property
    def total(self) -> float:
        return self.tavily_usd + self.openai_usd


class CostTracker:
    """Thread-safe async cost tracker with daily budget enforcement."""

    def __init__(self, daily_budget_usd: float, alert_threshold_usd: float) -> None:
        self._daily_budget = daily_budget_usd
        self._alert_threshold = alert_threshold_usd
        self._lock = asyncio.Lock()
        self._costs = CostBreakdown()

    async def add_cost(self, service: str, amount_usd: float) -> None:
        async with self._lock:
            if service == "tavily":
                self._costs.tavily_usd += amount_usd
            elif service == "openai":
                self._costs.openai_usd += amount_usd
            else:
                return

    async def get_totals(self) -> CostBreakdown:
        async with self._lock:
            return CostBreakdown(
                tavily_usd=self._costs.tavily_usd,
                openai_usd=self._costs.openai_usd,
            )

    async def within_budget(self, extra_cost_usd: float = 0.0) -> bool:
        totals = await self.get_totals()
        return (totals.total + extra_cost_usd) <= self._daily_budget

    @property
    def daily_budget(self) -> float:
        return self._daily_budget

    @property
    def alert_threshold(self) -> float:
        return self._alert_threshold
