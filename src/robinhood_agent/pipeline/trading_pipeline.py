"""Pipeline that loads inputs, runs the lifecycle, and persists reports."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from robinhood_agent.agents.orchestrator import OrchestratorAgent
from robinhood_agent.llm.client import LLMClient
from robinhood_agent.market.base import NewsProvider
from robinhood_agent.memory import (
    CalibrationReport,
    FeedbackLabel,
    MemoryStore,
    calibrate_threshold,
)
from robinhood_agent.models.context import MarketSnapshot, TradingResult
from robinhood_agent.models.market import (
    Instrument,
    MacroIndicators,
    NewsItem,
    PriceBar,
    Quote,
)
from robinhood_agent.models.portfolio import (
    Account,
    Portfolio,
    Position,
    RecentSale,
    TradingGoals,
)
from robinhood_agent.utils.config import EngineConfig, load_config
from robinhood_agent.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RunInput:
    """Normalized input for one trading run."""

    portfolio: Portfolio
    goals: TradingGoals
    snapshot: MarketSnapshot
    enrichment: dict[str, Any] = field(default_factory=dict)


def _build_snapshot(market: dict[str, Any]) -> MarketSnapshot:
    instruments = {
        item["symbol"]: Instrument.model_validate(item)
        for item in market.get("instruments", [])
    }
    quotes = {
        item["symbol"]: Quote.model_validate(item) for item in market.get("quotes", [])
    }
    bars = {
        symbol: [PriceBar.model_validate(bar) for bar in bar_list]
        for symbol, bar_list in market.get("bars", {}).items()
    }
    news = {
        symbol: [NewsItem.model_validate(item) for item in item_list]
        for symbol, item_list in market.get("news", {}).items()
    }
    macro_raw = market.get("macro")
    macro = MacroIndicators.model_validate(macro_raw) if macro_raw else None
    return MarketSnapshot(
        as_of=market.get("as_of"),
        instruments=instruments,
        quotes=quotes,
        bars=bars,
        news=news,
        macro=macro,
    )


def _hydrate_positions(portfolio: Portfolio, snapshot: MarketSnapshot) -> None:
    """Fill missing sector and current price on positions from the snapshot."""
    for position in portfolio.positions:
        if position.sector == "unknown":
            position.sector = snapshot.sector_of(position.symbol)
        if position.current_price <= 0.0:
            quote = snapshot.quote(position.symbol)
            if quote is not None:
                position.current_price = quote.price


def load_run_from_json(path: str | Path) -> RunInput:
    """Load a single trading run from a JSON file."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Run input JSON must be an object.")

    account = Account.model_validate(raw["portfolio"]["account"])
    positions = [
        Position.model_validate(item)
        for item in raw["portfolio"].get("positions", [])
    ]
    recent_sales = [
        RecentSale.model_validate(item)
        for item in raw["portfolio"].get("recent_sales", [])
    ]
    portfolio = Portfolio(
        account=account, positions=positions, recent_sales=recent_sales
    )
    goals = TradingGoals.model_validate(raw.get("goals", {}))
    snapshot = _build_snapshot(raw.get("market", {}))
    _hydrate_positions(portfolio, snapshot)
    return RunInput(
        portfolio=portfolio,
        goals=goals,
        snapshot=snapshot,
        enrichment=raw.get("enrichment", {}) or {},
    )


class TradingPipeline:
    """Coordinates a trading run end to end."""

    def __init__(
        self,
        config: EngineConfig | None = None,
        llm_client: LLMClient | None = None,
        memory_store: MemoryStore | None = None,
        news_provider: NewsProvider | None = None,
    ) -> None:
        self.config = config or load_config()
        self.memory_store = memory_store or self._build_memory_store()
        self.orchestrator = OrchestratorAgent(
            self.config,
            llm_client=llm_client,
            memory_store=self.memory_store,
            news_provider=news_provider,
        )

    def _build_memory_store(self) -> MemoryStore | None:
        if not self.config.memory.enabled:
            return None
        return MemoryStore(self.config.memory.path)

    def run(self, run_input: RunInput) -> TradingResult:
        return self.orchestrator.run(
            portfolio=run_input.portfolio,
            goals=run_input.goals,
            snapshot=run_input.snapshot,
            enrichment=run_input.enrichment,
        )

    def run_file(
        self, path: str | Path, output_dir: str | Path | None = None
    ) -> TradingResult:
        run_input = load_run_from_json(path)
        result = self.run(run_input)
        if output_dir is not None:
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            report_file = out_path / f"{result.run_id}.json"
            report_file.write_text(json.dumps(result.report, indent=2), encoding="utf-8")
            logger.info("Report written to %s", report_file)
        return result

    def record_feedback(
        self, proposal_id: str, label: FeedbackLabel, note: str | None = None
    ) -> bool:
        if self.memory_store is None:
            raise RuntimeError(
                "Collective memory is disabled. Enable memory in configuration to "
                "record feedback."
            )
        return self.memory_store.record_feedback(proposal_id, label, note)

    def calibrate(self) -> CalibrationReport:
        if self.memory_store is None:
            raise RuntimeError(
                "Collective memory is disabled. Enable memory in configuration to "
                "calibrate the approval threshold."
            )
        return calibrate_threshold(
            self.memory_store.all_records(), self.config.decision_policy
        )
