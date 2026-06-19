# Risk Limits

The risk guardian enforces these limits deterministically. Each check emits at most
one finding with a severity (0-100), a blocking flag, and a rationale. Thresholds
live in `config/config.yaml`; they are never hardcoded in logic.

## Blocking checks

| Check | Limit (default) | Applies to | Severity | Rationale |
| --- | --- | --- | --- | --- |
| Market hours | regular US session (9:30-16:00 ET), trading days only | all | 100 | Orders outside the open session (weekends, holidays, extended hours) are vetoed. |
| Position size — order notional | order notional <= 25,000 | buy and sell | 95 | A single order above the cap is a fat-finger and concentration risk. |
| Position size — projected weight | projected weight <= min(20% config, goal cap) | buy | 90 | A buy must not push a name above the per-position cap. |
| Concentration | projected sector weight <= 40% | buy | 85 | A buy must not push a sector above its cap. |
| Daily loss (kill switch) | intraday drawdown < 5% | buy | 100 | New risk is halted after the daily-loss threshold; exits are still allowed. |
| Order rate | orders per run <= 10 | all | 80 | Caps the number of orders a single run can emit. |
| Price deviation | limit within 10% of last price | limit orders | 90 | Guards against a mispriced limit order. |
| Buying power | notional <= cash less buffer | buy | 88 | A buy must not consume the cash buffer. |
| Pattern day trader | day trades <= 3 when not flagged | all | 85 | Avoids triggering the PDT rule for non-PDT accounts. |

A blocking finding vetoes the order when `decision_policy.block_on_critical` is true
(the default). Conviction never overrides a blocking finding.

## Advisory check

| Check | Limit (default) | Severity | Notes |
| --- | --- | --- | --- |
| Wash sale | no loss repurchase within 30 days | 50 | Non-blocking by default (tax treatment, not trade safety); can be made blocking. |
| Liquidity — volatility | daily stdev <= 0.08 | 65 | Non-blocking; raises the risk score. |
| Liquidity — spread | spread <= 1.0% | 55 | Non-blocking; raises the risk score. |
| Liquidity — volume | average volume >= 100,000 | 50 | Non-blocking; raises the risk score. |

## Decision mapping

- Aggregate risk score = the maximum finding severity (conservative).
- Any blocking finding (with block-on-critical) -> BLOCK.
- Otherwise, manual-approval forced or score >= approval threshold (default 40) ->
  REQUIRE_APPROVAL.
- Otherwise -> ALLOW.

## Environment overrides

`RISK_APPROVAL_THRESHOLD` and `RISK_BLOCK_ON_CRITICAL` adjust the decision policy
without code changes. All other limits are edited in `config/config.yaml`.

US-market context for these checks (sessions, the PDT rule, T+1 settlement, and the
wash-sale rule) is described in `us-market-conventions.md`.
