"""Thematic strategy: build exposure to conviction themes."""

from __future__ import annotations

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import Side, StrategySignal
from robinhood_agent.strategies.base import Strategy, StrategyOutput


class ThematicStrategy(Strategy):
    """Adds new names that match the investor's conviction themes.

    For each theme in ``goals.themes`` the strategy finds instruments in that sector
    that are not yet held and proposes an initial position sized to the configured
    per-name target, up to a cap on the number of new names per run.
    """

    name = "thematic"

    def generate(self, context: TradingContext) -> StrategyOutput:
        settings = self.config.strategy.thematic
        out = StrategyOutput()
        if not context.goals.themes:
            return out

        added = 0
        for theme in context.goals.themes:
            for symbol in context.snapshot.symbols_in_sector(theme):
                if added >= settings.max_new_names:
                    break
                if context.portfolio.position_for(symbol) is not None:
                    continue
                quote = context.snapshot.quote(symbol)
                if quote is None:
                    continue
                quantity = self._tranche_quantity(
                    context, quote.price, settings.per_name_target_pct
                )
                if quantity <= 0.0:
                    continue
                rationale = (
                    f"Add {symbol} for theme '{theme}': initial "
                    f"{settings.per_name_target_pct:.1%} position ({quantity:.0f} share(s))."
                )
                out.signals.append(
                    StrategySignal(strategy=self.name, symbol=symbol, action="buy",
                                   strength=0.6, rationale=rationale,
                                   evidence={"theme": theme})
                )
                out.proposals.append(
                    self._make_proposal(symbol, Side.BUY, quantity, quote.price,
                                        rationale, confidence=0.6)
                )
                added += 1
        return out
