"""Advisory approval-threshold calibration from labeled trade outcomes.

Calibration is deterministic and advisory only. It never mutates configuration; it
recommends an approval threshold that would have separated analyst-confirmed good
trades from bad ones, given their recorded risk scores. The goal is for bad trades
to land above the threshold (routed to human approval) and good trades below it.
"""

from __future__ import annotations

from robinhood_agent.memory.models import (
    CalibrationReport,
    FeedbackLabel,
    TradeMemoryRecord,
)
from robinhood_agent.utils.config import DecisionPolicy


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def calibrate_threshold(
    records: list[TradeMemoryRecord], policy: DecisionPolicy
) -> CalibrationReport:
    """Recommend an approval threshold from labeled trade risk scores."""
    good = [r.risk_score for r in records if r.label is FeedbackLabel.GOOD_TRADE]
    bad = [r.risk_score for r in records if r.label is FeedbackLabel.BAD_TRADE]

    report = CalibrationReport(
        labeled_trades=len(good) + len(bad),
        good_trades=len(good),
        bad_trades=len(bad),
        current_approval_threshold=policy.approval_threshold,
    )

    if not good or not bad:
        report.rationale.append(
            "At least one good-trade and one bad-trade label are required to "
            "recommend a threshold. No change suggested."
        )
        return report

    highest_good = max(good)
    lowest_bad = min(bad)

    if lowest_bad > highest_good:
        threshold = (lowest_bad + highest_good) / 2
        report.rationale.append(
            f"Labels are separable: good trades top out at risk {highest_good:.1f} "
            f"and bad trades start at {lowest_bad:.1f}. Suggested approval threshold "
            f"is their midpoint."
        )
    else:
        threshold = highest_good
        report.rationale.append(
            f"Labels overlap between {highest_good:.1f} (good) and {lowest_bad:.1f} "
            f"(bad). Suggested approval threshold favors catching bad trades for "
            f"review."
        )

    report.suggested_approval_threshold = round(_clamp(threshold), 1)
    report.rationale.append(
        "Recommendation is advisory only; thresholds in configuration are unchanged."
    )
    return report
