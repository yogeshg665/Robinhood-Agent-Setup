"""SQLite-backed collective memory for trade decisions.

The store persists trade decisions, recalls prior decisions for a symbol or
strategy, and records analyst feedback. It uses the standard-library ``sqlite3``
module so no extra dependency is required, and all operations are deterministic.
The memory signal is advisory: it never blocks an order on its own.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from robinhood_agent.memory.models import (
    FeedbackLabel,
    RecallSummary,
    TradeMemoryRecord,
)
from robinhood_agent.models.decision import TradeDecision
from robinhood_agent.models.proposal import OrderProposal
from robinhood_agent.utils.logging import get_logger

logger = get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS trade_memory (
    proposal_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,
    side TEXT NOT NULL,
    outcome TEXT NOT NULL,
    risk_score REAL NOT NULL,
    narrative TEXT NOT NULL,
    label TEXT NOT NULL,
    label_note TEXT,
    recorded_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_trade_memory_symbol ON trade_memory(symbol);
CREATE INDEX IF NOT EXISTS idx_trade_memory_strategy ON trade_memory(strategy);
"""


class MemoryStore:
    """A small, deterministic trade memory backed by SQLite."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # -- persistence -------------------------------------------------------

    def record_decision(
        self, run_id: str, proposal: OrderProposal, decision: TradeDecision
    ) -> TradeMemoryRecord:
        """Persist a single trade decision, preserving any existing label."""
        existing = self._get(proposal.proposal_id)
        record = TradeMemoryRecord(
            proposal_id=proposal.proposal_id,
            run_id=run_id,
            symbol=proposal.symbol,
            strategy=proposal.strategy,
            side=proposal.side.value,
            outcome=decision.outcome.value,
            risk_score=decision.risk_score,
            narrative=decision.narrative,
            label=existing.label if existing else FeedbackLabel.UNREVIEWED,
            label_note=existing.label_note if existing else None,
            recorded_at=datetime.now(timezone.utc),
        )
        self._upsert(record)
        return record

    def _upsert(self, record: TradeMemoryRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO trade_memory (
                proposal_id, run_id, symbol, strategy, side, outcome,
                risk_score, narrative, label, label_note, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(proposal_id) DO UPDATE SET
                run_id=excluded.run_id,
                symbol=excluded.symbol,
                strategy=excluded.strategy,
                side=excluded.side,
                outcome=excluded.outcome,
                risk_score=excluded.risk_score,
                narrative=excluded.narrative,
                label=excluded.label,
                label_note=excluded.label_note,
                recorded_at=excluded.recorded_at
            """,
            (
                record.proposal_id,
                record.run_id,
                record.symbol,
                record.strategy,
                record.side,
                record.outcome,
                record.risk_score,
                record.narrative,
                record.label.value,
                record.label_note,
                record.recorded_at.isoformat(),
            ),
        )
        self._conn.commit()

    # -- recall ------------------------------------------------------------

    def recall_for_symbol(self, symbol: str) -> RecallSummary:
        """Summarize prior decisions for a symbol."""
        rows = self._conn.execute(
            "SELECT * FROM trade_memory WHERE symbol = ? "
            "ORDER BY recorded_at DESC, proposal_id ASC",
            (symbol,),
        ).fetchall()
        if not rows:
            return RecallSummary()

        good = sum(1 for r in rows if r["label"] == FeedbackLabel.GOOD_TRADE.value)
        bad = sum(1 for r in rows if r["label"] == FeedbackLabel.BAD_TRADE.value)
        blocked = sum(1 for r in rows if r["outcome"] == "block")
        most_recent = rows[0]
        return RecallSummary(
            matched_on="symbol",
            total_prior=len(rows),
            good_trades=good,
            bad_trades=bad,
            blocked_count=blocked,
            most_recent_outcome=most_recent["outcome"],
            most_recent_at=self._parse_dt(most_recent["recorded_at"]),
        )

    # -- feedback ----------------------------------------------------------

    def record_feedback(
        self, proposal_id: str, label: FeedbackLabel, note: str | None = None
    ) -> bool:
        """Attach a label to a stored decision. Returns False if unknown."""
        cursor = self._conn.execute(
            "UPDATE trade_memory SET label = ?, label_note = ? WHERE proposal_id = ?",
            (label.value, note, proposal_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    # -- queries -----------------------------------------------------------

    def all_records(self) -> list[TradeMemoryRecord]:
        rows = self._conn.execute(
            "SELECT * FROM trade_memory ORDER BY recorded_at ASC, proposal_id ASC"
        ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def stats(self) -> dict:
        rows = self._conn.execute(
            "SELECT label, COUNT(*) AS n FROM trade_memory GROUP BY label"
        )
        by_label = {row["label"]: row["n"] for row in rows}
        return {"total": sum(by_label.values()), "by_label": by_label}

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> MemoryStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # -- helpers -----------------------------------------------------------

    def _get(self, proposal_id: str) -> TradeMemoryRecord | None:
        row = self._conn.execute(
            "SELECT * FROM trade_memory WHERE proposal_id = ?", (proposal_id,)
        ).fetchone()
        return self._row_to_record(row) if row else None

    @staticmethod
    def _parse_dt(value: str) -> datetime:
        return datetime.fromisoformat(value)

    def _row_to_record(self, row: sqlite3.Row) -> TradeMemoryRecord:
        return TradeMemoryRecord(
            proposal_id=row["proposal_id"],
            run_id=row["run_id"],
            symbol=row["symbol"],
            strategy=row["strategy"],
            side=row["side"],
            outcome=row["outcome"],
            risk_score=row["risk_score"],
            narrative=row["narrative"],
            label=FeedbackLabel(row["label"]),
            label_note=row["label_note"],
            recorded_at=self._parse_dt(row["recorded_at"]),
        )
