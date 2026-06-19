"""Models for the trading agent's collective memory."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class FeedbackLabel(str, Enum):
    """Analyst-confirmed quality of a past trade decision."""

    UNREVIEWED = "unreviewed"
    GOOD_TRADE = "good_trade"
    BAD_TRADE = "bad_trade"


class TradeMemoryRecord(BaseModel):
    """A persisted record of one trade decision."""

    proposal_id: str
    run_id: str
    symbol: str
    strategy: str
    side: str
    outcome: str
    risk_score: float
    narrative: str = ""
    label: FeedbackLabel = FeedbackLabel.UNREVIEWED
    label_note: str | None = None
    recorded_at: datetime


class RecallSummary(BaseModel):
    """Aggregated prior decisions for a symbol or strategy."""

    matched_on: str = "none"
    total_prior: int = 0
    good_trades: int = 0
    bad_trades: int = 0
    blocked_count: int = 0
    most_recent_outcome: str | None = None
    most_recent_at: datetime | None = None

    @property
    def has_history(self) -> bool:
        return self.total_prior > 0

    def as_enrichment(self) -> dict:
        return {
            "matched_on": self.matched_on,
            "total_prior": self.total_prior,
            "good_trades": self.good_trades,
            "bad_trades": self.bad_trades,
            "blocked_count": self.blocked_count,
            "most_recent_outcome": self.most_recent_outcome,
            "most_recent_at": (
                self.most_recent_at.isoformat() if self.most_recent_at else None
            ),
        }


class CalibrationReport(BaseModel):
    """Advisory recommendation for the approval threshold from labeled trades."""

    labeled_trades: int = 0
    good_trades: int = 0
    bad_trades: int = 0
    current_approval_threshold: float = 0.0
    suggested_approval_threshold: float | None = None
    rationale: list[str] = Field(default_factory=list)
