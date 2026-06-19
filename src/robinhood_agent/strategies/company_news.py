"""Company-news strategy: trade on deterministic daily-news sentiment.

The market-enrichment agent fetches news for each ``goals.news_targets`` symbol and
stores an aggregated sentiment summary in
``context.enrichment["news_sentiment"][symbol]``. This strategy reads that summary
and turns strong sentiment into a small directional proposal. It performs no I/O,
so it stays deterministic; news can only nudge proposals, never risk decisions.
"""

from __future__ import annotations

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import Side, StrategySignal
from robinhood_agent.strategies.base import Strategy, StrategyOutput


class CompanyNewsStrategy(Strategy):
    """Generates buys on strongly positive news and exits on strongly negative news."""

    name = "company_news"

    def generate(self, context: TradingContext) -> StrategyOutput:
        settings = self.config.strategy.news
        out = StrategyOutput()
        summaries = context.enrichment.get("news_sentiment", {})
        if not isinstance(summaries, dict):
            return out

        for symbol, summary in summaries.items():
            if not isinstance(summary, dict):
                continue
            avg = float(summary.get("average_sentiment", 0.0))
            count = int(summary.get("article_count", 0))
            if count == 0:
                continue
            quote = context.snapshot.quote(symbol)
            if quote is None:
                continue
            held = context.portfolio.position_for(symbol)

            if avg >= settings.positive_strength:
                quantity = self._tranche_quantity(context, quote.price, 0.04)
                if quantity <= 0.0:
                    continue
                rationale = (
                    f"{symbol} daily news sentiment {avg:+.2f} across {count} "
                    f"article(s) is strongly positive; add a small position."
                )
                out.signals.append(
                    StrategySignal(strategy=self.name, symbol=symbol, action="buy",
                                   strength=min(1.0, avg), rationale=rationale,
                                   evidence={"average_sentiment": round(avg, 2),
                                             "articles": count})
                )
                out.proposals.append(
                    self._make_proposal(symbol, Side.BUY, quantity, quote.price,
                                        rationale, confidence=0.5)
                )
            elif avg <= -settings.negative_strength and held and held.quantity > 0:
                rationale = (
                    f"{symbol} daily news sentiment {avg:+.2f} across {count} "
                    f"article(s) is strongly negative; reduce exposure."
                )
                quantity = float(int(held.quantity))
                out.signals.append(
                    StrategySignal(strategy=self.name, symbol=symbol, action="sell",
                                   strength=min(1.0, abs(avg)), rationale=rationale,
                                   evidence={"average_sentiment": round(avg, 2),
                                             "articles": count})
                )
                out.proposals.append(
                    self._make_proposal(symbol, Side.SELL, quantity, quote.price,
                                        rationale, confidence=0.5)
                )
        return out
