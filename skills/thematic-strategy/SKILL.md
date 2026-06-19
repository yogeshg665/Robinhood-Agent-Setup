---
name: thematic-strategy
description: Build initial exposure to conviction themes by adding new names in a target sector that are not yet held. WHEN: "invest in this theme", "add exposure to a sector", "build a position in healthcare", "thematic tilt", "buy names in my theme", "start a thematic basket".
---

# Thematic Strategy

## Overview

A strategy that builds exposure to the investor's conviction themes. For each theme
(a sector), it finds instruments in that sector that are not yet held and proposes
an initial position sized to the configured per-name target, up to a cap on new
names per run.

## When to Use

- During the strategy swarm, whenever `goals.themes` are defined.
- Do NOT use it to add to existing positions; it only initiates new names.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `goals.themes` | yes | Sectors the investor wants exposure to. |
| `config.strategy.thematic` | yes | Per-name target weight and the new-name cap. |

## Process

1. For each theme, list snapshot instruments in that sector.
2. Skip names already held.
3. Size an initial whole-share position to the per-name target weight.
4. Stop once the per-run new-name cap is reached.

## Outputs

Buy `OrderProposal` objects for new thematic names, each citing the theme and the
target size.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Add the whole theme at once." | The new-name cap limits how many names enter per run; the rest wait. |

## Red Flags

- A proposal for a name already held.
- More new names than the configured cap.

## Verification

- Every proposal is a new, unheld name in a requested theme.
- The number of new names does not exceed the cap.
