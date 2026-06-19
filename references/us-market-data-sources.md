# US Market Data Sources

The engine is deterministic and offline by default: every quote, bar, news item, and
macro indicator is part of the run snapshot, so a run is fully reproducible. This
document describes the US data sources the provider interfaces are designed to wrap
when an operator chooses to go live. Live providers are gated stubs — like the
Robinhood MCP broker, they refuse to run unless explicitly configured with
credentials, so the engine never makes a surprise network call.

## Provider seams

| Interface | Default (offline) | Live seam |
| --- | --- | --- |
| `MarketDataProvider` | `SnapshotMarketDataProvider` (reads the snapshot) | `LiveMarketDataProvider` (disabled stub) |
| `NewsProvider` | `OfflineNewsProvider` (reads the snapshot) | `LiveNewsProvider` (disabled stub) |

Select a provider with `market_data.provider` (`offline` | `live`) and
`strategy.news.provider` (`offline` | `live`), or the `MARKET_DATA_PROVIDER` /
`NEWS_PROVIDER` environment variables.

## Intended US vendors

These are common US-market vendors a live deployment can wire behind the interfaces.
This project does not bundle, endorse, or require any of them; respect each vendor's
license, rate limits, and terms.

| Data | Vendor options | Notes |
| --- | --- | --- |
| Quotes and daily OHLCV | Yahoo Finance, Alpha Vantage, Polygon.io, Nasdaq Data Link | Use the consolidated US tape; delayed data is fine for this engine. |
| Corporate news / sentiment | Vendor news APIs, company IR feeds | Sentiment is re-scored deterministically by the engine's lexicon. |
| Macro indicators | FRED (US Treasury yields, fed funds), CBOE (VIX), ICE (DXY) | Feed `snapshot.macro`; drives the regime layer. |
| Reference / fundamentals | SEC EDGAR | Public US filings for sector and identity mapping. |
| Benchmark | SPY (or `^GSPC`) | Used for relative strength and one-day alpha. |

## Credentials

Live vendors read credentials from the environment only; nothing is hardcoded or
committed. Typical variables:

- `MARKET_DATA_VENDOR`, `MARKET_DATA_API_KEY`
- `ALPHA_VANTAGE_API_KEY`, `POLYGON_API_KEY`, `FRED_API_KEY`
- `NEWS_API_KEY`

## Determinism contract

Whatever the source, the engine's contract is unchanged: data may inform strategy
proposals and the advisory macro regime, but it never alters a risk finding or a
trade decision. To keep a run reproducible, pin the snapshot (the offline default)
rather than pulling live data that moves between runs.
