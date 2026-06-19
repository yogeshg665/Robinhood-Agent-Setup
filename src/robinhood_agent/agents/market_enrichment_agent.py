"""Market-enrichment agent: derive metrics and aggregate company news.

This agent attaches derived context that strategies consume: portfolio weights,
per-symbol price-return summaries, and an aggregated daily-news sentiment summary
for each ``goals.news_targets`` symbol. News is fetched through the configured
provider and scored deterministically; it only informs strategy proposals.
"""

from __future__ import annotations

from datetime import datetime, timezone

from robinhood_agent.agents.base import Agent
from robinhood_agent.market.base import NewsProvider
from robinhood_agent.market.news import build_news_provider, score_sentiment
from robinhood_agent.models.context import TradingContext


class MarketEnrichmentAgent(Agent):
    """Computes derived market context and a deterministic news-sentiment summary."""

    name = "market_enrichment"

    def __init__(self, config, news_provider: NewsProvider | None = None) -> None:
        super().__init__(config)
        self._news_provider = news_provider

    def run(self, context: TradingContext) -> TradingContext:
        provider = self._news_provider or build_news_provider(
            self.config.strategy.news.provider, context.snapshot
        )
        lookback = self.config.strategy.news.lookback_hours

        news_summary: dict[str, dict] = {}
        for symbol in context.goals.news_targets:
            try:
                items = provider.get_news(symbol, lookback)
            except RuntimeError as exc:
                self.logger.warning("News fetch skipped for %s: %s", symbol, exc)
                continue
            if not items:
                continue
            scores = [score_sentiment(item) for item in items]
            average = sum(scores) / len(scores)
            news_summary[symbol] = {
                "average_sentiment": round(average, 4),
                "article_count": len(items),
                "latest_headline": items[0].headline,
            }

        portfolio_weights = {
            position.symbol: round(context.portfolio.weight_of(position.symbol), 4)
            for position in context.portfolio.positions
        }

        derived = {
            "as_of": context.snapshot.as_of or datetime.now(timezone.utc).isoformat(),
            "portfolio_weights": portfolio_weights,
            "total_value": round(context.portfolio.total_value, 2),
            "news_sentiment": news_summary,
        }
        # Caller-provided enrichment wins over derived defaults.
        context.enrichment = {**derived, **context.enrichment}
        self.logger.info(
            "Enrichment complete: %d news target(s) summarized", len(news_summary)
        )
        return context
