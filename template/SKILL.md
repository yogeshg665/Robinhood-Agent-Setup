---
name: skill-name
description: A clear, complete description of what this skill does and the exact conditions under which an agent should invoke it. Start with the capability, then list trigger phrases. WHEN: "trigger phrase one", "trigger phrase two".
---

# Skill Name

## Overview

One or two sentences stating the purpose of this skill and the outcome it
produces.

## When to Use

- Concrete condition that should activate this skill.
- Another concrete condition.
- Explicitly note conditions where this skill should NOT be used.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `field_name` | yes | What it is and where it comes from. |

## Process

1. First concrete step the agent performs.
2. Next step, with the decision or computation involved.
3. Continue until the skill produces its output.

## Outputs

Describe the structured result this skill returns and how downstream skills
consume it.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "This check can be skipped for a tiny order." | State why the step is still required. |

## Red Flags

- Signs that the skill is being applied incorrectly or producing unreliable output.

## Verification

- Evidence that must exist before the skill is considered complete (for example,
  a populated output field, a passing test, or a logged rationale).
