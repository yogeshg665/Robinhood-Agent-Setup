"""News providers and a deterministic sentiment scorer.

The offline provider serves news from the run snapshot, so company-news signals
are reproducible. A live provider is intentionally a disabled stub: it requires
explicit configuration and credentials and otherwise refuses to run, so the engine
never makes a surprise network call.

Sentiment is scored deterministically from a fixed keyword lexicon when a news
item does not already carry a sentiment score. News can only influence strategy
proposals; it never changes a risk finding or a trade decision.
"""

from __future__ import annotations

from robinhood_agent.market.base import NewsProvider
from robinhood_agent.models.context import MarketSnapshot
from robinhood_agent.models.market import NewsItem
from robinhood_agent.utils.logging import get_logger

logger = get_logger(__name__)

_POSITIVE_TERMS = (
    "beats",
    "beat",
    "record",
    "surge",
    "upgrade",
    "raises",
    "raised",
    "growth",
    "approval",
    "wins",
    "win",
    "expansion",
    "outperform",
    "strong",
)
_NEGATIVE_TERMS = (
    "miss",
    "misses",
    "downgrade",
    "cut",
    "cuts",
    "probe",
    "lawsuit",
    "recall",
    "decline",
    "weak",
    "loss",
    "fraud",
    "investigation",
    "warns",
    "warning",
    "layoffs",
)


def score_sentiment(item: NewsItem) -> float:
    """Return a deterministic sentiment in [-1, 1] for a news item.

    Pre-scored items are returned as-is. Otherwise the headline and summary are
    scanned against a fixed lexicon and the net term count is normalized.
    """
    if item.sentiment is not None:
        return item.sentiment
    text = f"{item.headline} {item.summary}".lower()
    positives = sum(1 for term in _POSITIVE_TERMS if term in text)
    negatives = sum(1 for term in _NEGATIVE_TERMS if term in text)
    total = positives + negatives
    if total == 0:
        return 0.0
    return max(-1.0, min(1.0, (positives - negatives) / total))


class OfflineNewsProvider(NewsProvider):
    """Serves news headlines from the deterministic run snapshot."""

    def __init__(self, snapshot: MarketSnapshot) -> None:
        self.snapshot = snapshot

    def get_news(self, symbol: str, lookback_hours: int) -> list[NewsItem]:
        items = list(self.snapshot.news_for(symbol))
        items.sort(key=lambda news: news.published_at, reverse=True)
        return items


class LiveNewsProvider(NewsProvider):
    """Disabled stub for a live news API.

    This provider deliberately refuses to run unless an API key is supplied, so the
    engine never performs an unexpected network call. Wire a real client here behind
    your own credentials and rate limits.
    """

    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key

    def get_news(self, symbol: str, lookback_hours: int) -> list[NewsItem]:
        raise RuntimeError(
            "Live news provider is not configured. Set NEWS_PROVIDER=offline to use "
            "fixtures, or implement LiveNewsProvider with NEWS_API_KEY before "
            "enabling live news."
        )


def build_news_provider(
    provider: str, snapshot: MarketSnapshot, api_key: str | None = None
) -> NewsProvider:
    """Construct the configured news provider. Defaults to the offline provider."""
    if provider == "live":
        logger.warning("Live news provider requested; ensure NEWS_API_KEY is set.")
        return LiveNewsProvider(api_key)
    return OfflineNewsProvider(snapshot)
