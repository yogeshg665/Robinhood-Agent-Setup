"""Paper broker: simulates fills and records a local blotter.

This is the default, safe execution path. No real funds are involved. Each approved
order is "filled" at its estimated price (or limit price) and appended to a local
JSON blotter so runs are inspectable and reproducible.
"""

from __future__ import annotations

import json
from pathlib import Path

from robinhood_agent.execution.base import BrokerAdapter, ExecutionReport
from robinhood_agent.models.proposal import OrderProposal, OrderType
from robinhood_agent.utils.logging import get_logger

logger = get_logger(__name__)


class PaperBroker(BrokerAdapter):
    """A deterministic simulator that fills orders at the estimated price."""

    venue = "paper"

    def __init__(self, state_path: str | Path | None = None) -> None:
        self.state_path = Path(state_path) if state_path else None

    def place_order(self, proposal: OrderProposal) -> ExecutionReport:
        fill_price = (
            proposal.limit_price
            if proposal.order_type is OrderType.LIMIT and proposal.limit_price
            else proposal.estimated_price
        )
        report = ExecutionReport(
            proposal_id=proposal.proposal_id,
            symbol=proposal.symbol,
            side=proposal.side.value,
            quantity=proposal.quantity,
            status="filled",
            venue=self.venue,
            filled_price=fill_price,
            detail="Simulated paper fill at estimated price.",
        )
        self._append_blotter(report)
        logger.info(
            "Paper fill: %s %s x%.0f @ %.2f",
            report.side,
            report.symbol,
            report.quantity,
            report.filled_price,
        )
        return report

    def _append_blotter(self, report: ExecutionReport) -> None:
        if self.state_path is None:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        blotter: list[dict] = []
        if self.state_path.exists():
            try:
                blotter = json.loads(self.state_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                blotter = []
        blotter.append(json.loads(report.model_dump_json()))
        self.state_path.write_text(json.dumps(blotter, indent=2), encoding="utf-8")
