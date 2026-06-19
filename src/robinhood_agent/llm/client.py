"""A thin, optional LLM client used only to refine narrative text.

The client is deterministic-safe: when no provider is configured or any error
occurs, ``summarize`` returns ``None`` and callers fall back to the deterministic
narrative. The LLM never influences a strategy proposal, a risk finding, or a
trade decision.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from robinhood_agent.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LLMSettings:
    """Resolved LLM configuration."""

    provider: str = "none"
    api_key: str | None = None
    model: str = "gpt-4o-mini"
    api_base: str | None = None

    @classmethod
    def from_env(cls) -> LLMSettings:
        return cls(
            provider=(os.getenv("LLM_PROVIDER") or "none").strip().lower(),
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL") or "gpt-4o-mini",
            api_base=os.getenv("OPENAI_API_BASE") or None,
        )

    @property
    def enabled(self) -> bool:
        return self.provider in {"openai", "azure_openai"} and bool(self.api_key)


class LLMClient:
    """Wraps an optional OpenAI-compatible client behind a safe interface."""

    def __init__(self, settings: LLMSettings | None = None) -> None:
        self.settings = settings or LLMSettings.from_env()

    def summarize(self, system_prompt: str, user_prompt: str) -> str | None:
        """Return a refined narrative, or ``None`` to use the deterministic text."""
        if not self.settings.enabled:
            return None
        try:
            from openai import OpenAI

            if self.settings.api_base:
                client = OpenAI(api_key=self.settings.api_key, base_url=self.settings.api_base)
            else:
                client = OpenAI(api_key=self.settings.api_key)

            response = client.chat.completions.create(
                model=self.settings.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content
        except Exception as exc:  # noqa: BLE001 - narrative is best-effort only
            logger.warning("LLM narrative refinement skipped: %s", exc)
            return None
