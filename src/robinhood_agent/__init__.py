"""AI Robinhood Agent (Quill): a deterministic, risk-governed equities trading agent.

A swarm of strategy agents proposes orders and an independent risk guardian has the
final say and can veto any order. Scoring and decisions are deterministic and
reproducible — a language model may enrich the narrative only. The engine runs in
paper (simulated) mode by default, with optional gated live execution through
Robinhood Agentic Trading (MCP).
"""

__version__ = "1.0.0"
