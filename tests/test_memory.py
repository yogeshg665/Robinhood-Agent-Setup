"""Tests for the optional collective-memory layer and advisory calibration."""

from __future__ import annotations

from datetime import datetime, timezone

from robinhood_agent.memory import (
    FeedbackLabel,
    MemoryStore,
    TradeMemoryRecord,
    calibrate_threshold,
)
from robinhood_agent.models.decision import DecisionOutcome, TradeDecision
from robinhood_agent.models.proposal import Side
from robinhood_agent.utils.config import DecisionPolicy
from tests.conftest import make_proposal


def test_record_and_recall(tmp_path) -> None:
    store = MemoryStore(str(tmp_path / "memory.db"))
    proposal = make_proposal("AAA", Side.BUY, 10, 100.0, strategy="momentum")
    decision = TradeDecision(
        proposal_id=proposal.proposal_id,
        symbol="AAA",
        outcome=DecisionOutcome.ALLOW,
        risk_score=10.0,
    )
    store.record_decision("run_1", proposal, decision)

    summary = store.recall_for_symbol("AAA")
    assert summary.has_history
    assert summary.total_prior == 1
    store.close()


def test_feedback_is_persisted(tmp_path) -> None:
    store = MemoryStore(str(tmp_path / "memory.db"))
    proposal = make_proposal("AAA", Side.BUY, 10, 100.0)
    decision = TradeDecision(
        proposal_id=proposal.proposal_id, symbol="AAA", outcome=DecisionOutcome.ALLOW
    )
    store.record_decision("run_1", proposal, decision)

    assert store.record_feedback(proposal.proposal_id, FeedbackLabel.GOOD_TRADE) is True
    assert store.record_feedback("missing", FeedbackLabel.GOOD_TRADE) is False

    summary = store.recall_for_symbol("AAA")
    assert summary.good_trades == 1
    store.close()


def _record(proposal_id: str, risk_score: float, label: FeedbackLabel) -> TradeMemoryRecord:
    return TradeMemoryRecord(
        proposal_id=proposal_id,
        run_id="run_1",
        symbol="AAA",
        strategy="momentum",
        side="buy",
        outcome="allow",
        risk_score=risk_score,
        label=label,
        recorded_at=datetime.now(timezone.utc),
    )


def test_calibration_suggests_threshold_between_classes() -> None:
    records = [
        _record("p1", 20.0, FeedbackLabel.GOOD_TRADE),
        _record("p2", 30.0, FeedbackLabel.GOOD_TRADE),
        _record("p3", 70.0, FeedbackLabel.BAD_TRADE),
        _record("p4", 80.0, FeedbackLabel.BAD_TRADE),
    ]
    report = calibrate_threshold(records, DecisionPolicy())
    assert report.suggested_approval_threshold is not None
    assert 30.0 <= report.suggested_approval_threshold <= 70.0


def test_calibration_requires_both_classes() -> None:
    records = [_record("p1", 20.0, FeedbackLabel.GOOD_TRADE)]
    report = calibrate_threshold(records, DecisionPolicy())
    assert report.suggested_approval_threshold is None
