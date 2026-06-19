"""End-to-end pipeline tests over the bundled synthetic sample."""

from __future__ import annotations

from pathlib import Path

from robinhood_agent.pipeline import TradingPipeline, load_run_from_json
from tests.conftest import build_config

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "samples" / "sample_run.json"


def test_load_run_hydrates_positions() -> None:
    run_input = load_run_from_json(SAMPLE)
    assert run_input.portfolio.positions
    for position in run_input.portfolio.positions:
        assert position.current_price > 0.0
        assert position.sector != "unknown"


def test_pipeline_produces_full_decision_mix() -> None:
    pipeline = TradingPipeline(config=build_config())
    result = pipeline.run(load_run_from_json(SAMPLE))
    counts = result.report["counts"]["by_outcome"]
    # The sample is designed to exercise every outcome.
    assert counts.get("allow", 0) >= 1
    assert counts.get("require_approval", 0) >= 1
    assert counts.get("block", 0) >= 1
    assert result.report["counts"]["proposals"] == len(result.decisions)


def test_pipeline_is_deterministic() -> None:
    pipeline = TradingPipeline(config=build_config())
    first = pipeline.run(load_run_from_json(SAMPLE)).report["counts"]
    second = pipeline.run(load_run_from_json(SAMPLE)).report["counts"]
    assert first == second


def test_reasoning_trail_is_present() -> None:
    pipeline = TradingPipeline(config=build_config())
    result = pipeline.run(load_run_from_json(SAMPLE))
    assert len(result.report["reasoning"]) == len(result.decisions)
