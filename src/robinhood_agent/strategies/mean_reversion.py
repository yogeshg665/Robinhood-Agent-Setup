"""Mean-reversion strategy: fade statistical extremes."""

from __future__ import annotations

import statistics

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import Side, StrategySignal
from robinhood_agent.strategies.base import Strategy, StrategyOutput


class MeanReversionStrategy(Strategy):
    """Buys oversold names and sells overbought ones using a close-price z-score.

    The z-score is computed from the lookback window of closing prices. A deeply
    negative z-score (oversold) generates a buy tranche; a strongly positive z-score
    (overbought) exits an existing position.
    """

    name = "mean_reversion"

    def generate(self, context: TradingContext) -> StrategyOutput:
        settings = self.config.strategy.mean_reversion
        out = StrategyOutput()
        universe = context.goals.watchlist or list(context.snapshot.quotes.keys())

        for symbol in universe:
            bars = context.snapshot.bars_for(symbol)
            if len(bars) < settings.lookback_bars:
                continue
            closes = [bar.close for bar in bars[-settings.lookback_bars :]]
            mean = statistics.fmean(closes)
            stdev = statistics.pstdev(closes)
            if stdev <= 0.0:
                continue
            quote = context.snapshot.quote(symbol)
            if quote is None:
                continue
            zscore = (quote.price - mean) / stdev
            held = context.portfolio.position_for(symbol)

            if zscore <= settings.zscore_buy:
                quantity = self._tranche_quantity(context, quote.price, 0.05)
                if quantity <= 0.0:
                    continue
                rationale = (
                    f"{symbol} trades {zscore:.1f} sigma below its "
                    f"{settings.lookback_bars}-bar mean ({mean:,.2f}); oversold buy."
                )
                out.signals.append(
                    StrategySignal(strategy=self.name, symbol=symbol, action="buy",
                                   strength=min(1.0, abs(zscore) / 4), rationale=rationale,
                                   evidence={"zscore": round(zscore, 2)})
                )
                out.proposals.append(
                    self._make_proposal(symbol, Side.BUY, quantity, quote.price,
                                        rationale, confidence=0.55)
                )
            elif zscore >= settings.zscore_sell and held and held.quantity > 0:
                rationale = (
                    f"{symbol} trades {zscore:.1f} sigma above its "
                    f"{settings.lookback_bars}-bar mean ({mean:,.2f}); overbought exit."
                )
                out.signals.append(
                    StrategySignal(strategy=self.name, symbol=symbol, action="sell",
                                   strength=min(1.0, zscore / 4), rationale=rationale,
                                   evidence={"zscore": round(zscore, 2)})
                )
                out.proposals.append(
                    self._make_proposal(symbol, Side.SELL, float(int(held.quantity)),
                                        quote.price, rationale, confidence=0.55)
                )
        return out
