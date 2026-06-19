"""Command-line interface for the AI Robinhood Agent."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from robinhood_agent.memory import FeedbackLabel
from robinhood_agent.pipeline import TradingPipeline
from robinhood_agent.utils.config import load_config

app = typer.Typer(
    add_completion=False,
    help="A deterministic, risk-governed equities trading agent (paper mode by default).",
)
console = Console()

_OUTCOME_STYLE = {
    "allow": "green",
    "require_approval": "yellow",
    "block": "red",
}


def _load_config_with_memory(config_path: str | None, memory_path: str | None):
    config = load_config(config_path)
    if memory_path:
        config.memory.enabled = True
        config.memory.path = memory_path
    return config


@app.command()
def run(
    input_file: str = typer.Argument(..., help="Path to a run input JSON file."),
    config_path: str | None = typer.Option(None, "--config", "-c", help="Config YAML."),
    output: str | None = typer.Option(None, "--output", "-o", help="Report output dir."),
    memory: str | None = typer.Option(
        None, "--memory", "-m", help="Enable collective memory at this SQLite path."
    ),
) -> None:
    """Run the trading lifecycle over one input file and print the decisions."""
    config = _load_config_with_memory(config_path, memory)
    pipeline = TradingPipeline(config=config)
    result = pipeline.run_file(input_file, output_dir=output)

    venue = result.report.get("execution_venue", "paper")
    console.print(
        f"[bold]Run {result.run_id}[/bold]  venue=[cyan]{venue}[/cyan]  "
        f"portfolio=[cyan]{result.report.get('portfolio_value', 0):,.2f}[/cyan]"
    )

    table = Table(title="Trade Decisions", show_lines=False)
    table.add_column("Symbol")
    table.add_column("Side")
    table.add_column("Qty", justify="right")
    table.add_column("Strategy")
    table.add_column("Notional", justify="right")
    table.add_column("Risk", justify="right")
    table.add_column("Decision")

    for row in result.report.get("decisions", []):
        outcome = row["outcome"]
        style = _OUTCOME_STYLE.get(outcome, "white")
        table.add_row(
            row["symbol"],
            row.get("side", ""),
            f"{row.get('quantity', 0):.0f}",
            row.get("strategy", ""),
            f"{row.get('estimated_notional', 0):,.0f}",
            f"{row.get('risk_score', 0):.0f}",
            f"[{style}]{outcome.replace('_', ' ').upper()}[/{style}]",
        )

    if result.report.get("decisions"):
        console.print(table)
    else:
        console.print("[dim]No proposals were generated for this run.[/dim]")
    console.print(f"[dim]{result.report.get('counts', {})}[/dim]")


@app.command()
def explain(
    input_file: str = typer.Argument(..., help="Path to a run input JSON file."),
    config_path: str | None = typer.Option(None, "--config", "-c"),
) -> None:
    """Print the full JSON report (including the reasoning trail) for a run."""
    pipeline = TradingPipeline(config=load_config(config_path))
    result = pipeline.run_file(input_file)
    console.print_json(json.dumps(result.report))


@app.command()
def feedback(
    proposal_id: str = typer.Argument(..., help="Proposal id to label."),
    label: str = typer.Argument(..., help="good_trade | bad_trade | unreviewed"),
    note: str | None = typer.Option(None, "--note", help="Optional note."),
    memory: str = typer.Option(..., "--memory", "-m", help="Memory SQLite path."),
) -> None:
    """Attach an analyst label to a previously recorded trade decision."""
    config = _load_config_with_memory(None, memory)
    pipeline = TradingPipeline(config=config)
    try:
        feedback_label = FeedbackLabel(label)
    except ValueError:
        console.print(f"[red]Invalid label '{label}'.[/red]")
        raise typer.Exit(code=1) from None
    updated = pipeline.record_feedback(proposal_id, feedback_label, note)
    if updated:
        console.print(f"[green]Recorded {label} for {proposal_id}.[/green]")
    else:
        console.print(f"[yellow]No stored decision with id {proposal_id}.[/yellow]")


@app.command()
def calibrate(
    memory: str = typer.Option(..., "--memory", "-m", help="Memory SQLite path."),
) -> None:
    """Recommend an approval threshold from labeled trade outcomes (advisory)."""
    config = _load_config_with_memory(None, memory)
    pipeline = TradingPipeline(config=config)
    report = pipeline.calibrate()

    table = Table(title="Advisory Threshold Calibration")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Labeled trades", str(report.labeled_trades))
    table.add_row("Good trades", str(report.good_trades))
    table.add_row("Bad trades", str(report.bad_trades))
    table.add_row("Current approval threshold", f"{report.current_approval_threshold:.1f}")
    suggested = (
        f"{report.suggested_approval_threshold:.1f}"
        if report.suggested_approval_threshold is not None
        else "n/a"
    )
    table.add_row("Suggested approval threshold", suggested)
    console.print(table)
    for line in report.rationale:
        console.print(f"[dim]- {line}[/dim]")


@app.command()
def validate_state(
    memory: str = typer.Option(..., "--memory", "-m", help="Memory SQLite path."),
) -> None:
    """Print simple statistics about the collective-memory store."""
    config = _load_config_with_memory(None, memory)
    pipeline = TradingPipeline(config=config)
    if pipeline.memory_store is None:
        console.print("[yellow]Memory is disabled.[/yellow]")
        raise typer.Exit(code=1)
    console.print_json(json.dumps(pipeline.memory_store.stats()))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
