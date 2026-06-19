# Contributing

Thank you for improving the AI Robinhood Agent. This project pairs an Agent
Skills pack with a deterministic Python engine that is the executable reference
for every skill.

## Ground Rules

1. **Determinism is mandatory.** Strategy proposals may be heuristic, but the
   risk-guardian findings and the final trade decision must be reproducible from
   the inputs. A language model may enrich narrative only; it must never change a
   risk finding or a decision.
2. **Safety first.** Live trading is disabled by default. Real orders require
   both `EXECUTION_MODE=robinhood_mcp` and `LIVE_TRADING_ENABLED=true`. Never
   commit credentials; read them from the environment only.
3. **The risk guardian has final say.** A blocking risk finding cannot be
   overridden by a strategy or by narrative.
4. **Synthetic data only.** Sample data must use fictional symbols, accounts, and
   prices. Never commit real account identifiers or personal data.

## Adding a Strategy

1. Create a module under `src/robinhood_agent/strategies/` that subclasses
   `Strategy` and returns `StrategySignal` and/or `OrderProposal` objects.
2. Register it in `strategies/registry.py`.
3. Add a matching `SKILL.md` under `skills/`.
4. Add tests under `tests/`.

## Adding a Risk Check

1. Create a module under `src/robinhood_agent/risk/` that subclasses `RiskCheck`
   and returns a `RiskFinding` (set `blocking=True` for hard limits).
2. Register it in `risk/registry.py`.
3. Add a matching `SKILL.md` and tests.

## Checks Before You Open a PR

```bash
python scripts/validate_skills.py
python -m ruff check src/robinhood_agent tests
python -m mypy src/robinhood_agent
python -m pytest -q
```

## Conventions

- Skill folder names are lowercase with hyphens and match the `name` field.
- Each risk check emits at most one finding with a severity, a blocking flag, and
  a rationale.
- Configuration lives in `config/config.yaml`; do not hardcode thresholds.
