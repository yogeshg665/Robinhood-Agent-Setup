#!/usr/bin/env python3
"""Validate every SKILL.md against the Agent Skills format.

Checks that each skill folder under skills/ contains a SKILL.md with valid YAML
frontmatter providing non-empty `name` and `description` fields, that the `name`
matches its folder, and that the body contains required sections. Exits non-zero
on any violation so the check can gate continuous integration.
"""

from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_FIELDS = ("name", "description")
REQUIRED_SECTIONS = ("## Overview", "## Process", "## Verification")
SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a markdown document into its frontmatter and body.

    Uses a lenient, line-based parse rather than a strict YAML loader because
    skill descriptions commonly contain colons (for example, ``WHEN: ...``),
    which is valid in this format but would break a strict YAML parser.
    """
    if not text.startswith("---"):
        raise ValueError("missing YAML frontmatter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("malformed YAML frontmatter delimiters")

    front: dict[str, str] = {}
    current_key: str | None = None
    for line in parts[1].splitlines():
        if not line.strip():
            continue
        stripped = line.lstrip()
        # A new top-level key is an unindented "key: value" line.
        if line == stripped and ":" in line:
            key, _, value = line.partition(":")
            current_key = key.strip()
            front[current_key] = value.strip()
        elif current_key is not None:
            # Continuation of a folded multi-line value.
            front[current_key] = f"{front[current_key]} {stripped}".strip()

    return front, parts[2]


def validate_skill(skill_md: Path) -> list[str]:
    """Return a list of error messages for a single SKILL.md (empty if valid)."""
    errors: list[str] = []
    folder = skill_md.parent.name
    try:
        front, body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    except ValueError as exc:
        return [f"{folder}: {exc}"]

    for field in REQUIRED_FIELDS:
        value = front.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{folder}: frontmatter field '{field}' is missing or empty")

    name = front.get("name")
    if isinstance(name, str) and name != folder:
        errors.append(f"{folder}: name '{name}' does not match folder name")

    for section in REQUIRED_SECTIONS:
        if section not in body:
            errors.append(f"{folder}: missing required section '{section}'")

    return errors


def main() -> int:
    if not SKILLS_DIR.is_dir():
        print(f"No skills directory found at {SKILLS_DIR}", file=sys.stderr)
        return 1

    skill_files = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    if not skill_files:
        print("No SKILL.md files found.", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    for skill_md in skill_files:
        all_errors.extend(validate_skill(skill_md))

    if all_errors:
        print("Skill validation failed:")
        for error in all_errors:
            print(f"  - {error}")
        return 1

    print(f"All {len(skill_files)} skills are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
