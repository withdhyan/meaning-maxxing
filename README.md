# meaning-maxxing

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) skill that
extracts your deeply held values from conversation and maintains a living
moral graph of what matters to you.

Built on the [Meaning Alignment Institute](https://meaningalignment.org)'s
[value-tools](https://github.com/meaningalignment/values-tools) methodology
and their Democratic Fine-Tuning research.

## The Problem

AI assistants know your preferences. They don't know your values.

Preferences are shallow: dark mode, tabs over spaces, concise answers.
Values are deep: what you attend to when something actually matters.
A preference tells the assistant what to do. A value tells it who you are.

Hermes Agent already maintains a `USER.md` — a profile that deepens across
sessions. But USER.md captures preferences and habits, not the structure of
meaning underneath. This skill adds that layer.

## What It Does

As you use Hermes, the agent notices value-laden moments — when you describe
something that moved you, make a difficult choice, talk about someone you
admire, or resist a suggestion. It silently extracts **sources of meaning**:
not preferences or goals, but the specific things you attend to when
something matters.

These are expressed as **attention policies** — the MAI's core representational
primitive:

> **Generative Honesty**
> - MOMENTS where telling a difficult truth opens a new possibility
> - SIGNS that someone is ready to hear what they need to hear
> - WAYS of speaking that make hard truths land as gifts rather than weapons

Values accumulate into a **moral graph** with wiser-than relationships,
PageRank scoring, and growth narratives. Your top values are rendered into
a concise summary in USER.md, giving Hermes a deepening understanding of
who you are across sessions.

## The Wisdom Score (TWS)

TWS is a composite metric that captures the maturity of your moral landscape.
It combines three dimensions, all required — you can't fake wisdom with
volume alone:

```
TWS = (Depth x Growth x Coherence) ^ (1/3)
```

| Dimension | Measures | Signal |
|-----------|----------|--------|
| **Depth** | How much PageRank concentrates in top values | Clear, strong commitments vs. diffuse noise |
| **Growth** | How many upgrade edges exist, weighted by confidence | Active moral evolution vs. static collection |
| **Coherence** | Fraction of values participating in at least one edge | Interconnected landscape vs. isolated fragments |

TWS is the geometric mean: all three must be nonzero for a positive score.
A person with many values but no growth scores zero. A person with growth
but no clear commitments scores zero. Wisdom requires depth AND evolution
AND integration.

```
$ values tws

The Wisdom Score: 0.61

- Depth: 0.72 — how strongly your deepest commitments stand out
- Growth: 0.58 — how much moral evolution has occurred
- Coherence: 0.55 — how interconnected your value landscape is
```

## Core Concepts

### Sources of Meaning (not "values")

The MAI distinguishes sources of meaning from the things people usually call
values. A source of meaning is NOT:

- A **preference**: "I like functional programming" (shallow, contextual)
- A **goal**: "I want to be promoted" (outcome-oriented, not way-of-being)
- A **moral principle**: "People should be honest" (abstract, normative)
- An **emotion**: "I felt angry" (transient, reactive)

A source of meaning IS a way of living that matters to someone, articulated
as things to **attend to**. The representational format is strict:

```
CAPITALIZED_PLURAL_NOUN qualifying phrase
```

Good: `MOMENTS where someone chooses growth over comfort`
Bad: `Being honest` (not attending to anything specific)
Bad: `HONESTY in relationships` (singular, abstract)

### The Moral Graph

Values don't exist in isolation. They grow.

**Wiser-than edges**: Value B may be a deeper version of Value A. "Generative
Honesty" might be wiser than "Radical Transparency" — same commitment to truth,
but with sensitivity to timing and reception.

**Upgrades**: When a wiser-than relationship is detected, the system generates
a narrative explaining the growth. Three patterns:

1. **Partial -> Whole**: The earlier value addressed only part of what mattered
2. **Impure -> Pure**: The earlier value was entangled with ego or fear
3. **Unskillful -> Skillful**: Right target, clumsier approach

**PageRank**: Values that are frequently "wiser than" others accumulate higher
rank, surfacing the user's deepest commitments. Damping factor 0.85,
100 iterations, confidence-weighted edges.

### Presence, Not Interrogation

The most important design principle: the agent is present, not extractive.

It doesn't interview you about your values. It doesn't optimize for extraction
volume. You came to it for help with something — it helps you. Values emerge
naturally from genuine engagement. The agent's role is to notice and honor
them, not to hunt for them.

When a value is extracted, the tool quietly updates your moral graph and
regenerates your USER.md summary. Your experience should be seamless — you
should feel understood, not studied.

This is the difference between surveillance and presence.

## Architecture

```
meaning-maxxing/
├── skill/
│   ├── SKILL.md                        # Skill definition — teaches Hermes the methodology
│   ├── prompts/
│   │   ├── extract_value.md            # Value articulation (zooming techniques)
│   │   ├── check_duplicate.md          # 5-criterion deduplication
│   │   ├── detect_upgrade.md           # Moral growth detection (3 upgrade patterns)
│   │   └── render_user_summary.md      # USER.md prose rendering (<800 chars)
│   └── scripts/
│       ├── __init__.py                 # Public API exports
│       ├── types.py                    # Value, Edge, Upgrade, MoralGraph, AttentionPolicy
│       ├── extractor.py               # LLM message builders + JSON response parsers
│       ├── store.py                    # JSON-backed graph persistence, PageRank, TWS
│       ├── renderer.py                # USER.md injection (marker-delimited, sanitized)
│       ├── tool.py                    # ValuesTool orchestrator (5 actions)
│       └── register.py               # Hermes ToolRegistry bridge (auto-registers)
├── tests/
│   ├── test_types.py                   # 15 tests: round-trip serialization, edge cases
│   ├── test_extractor.py              # 23 tests: JSON parsing, message building, response parsing
│   ├── test_store.py                  # 28 tests: CRUD, PageRank, TWS, persistence
│   ├── test_renderer.py              # 10 tests: injection, markers, sanitization
│   └── test_tool.py                   # 15 tests: dispatch, actions, mock LLM pipeline
├── install.sh                          # One-command installation
├── LICENSE                             # GPL-3.0
└── README.md
```

### Three Layers

| Layer | Primitive | File | Role |
|-------|-----------|------|------|
| **Knowledge** | Hermes Skill | `SKILL.md` | Teaches Hermes *when and why* to extract values — the five signals, the zooming techniques, the attention policy format, the cardinal rule of presence |
| **Execution** | Python Tool | `tool.py` + `store.py` | Runs the pipeline: extract -> deduplicate -> detect upgrades -> mutate graph -> render USER.md. Computes PageRank and TWS |
| **Surface** | USER.md | `renderer.py` | Injects a concise prose portrait between `<!-- values-start -->` / `<!-- values-end -->` markers. Full graph lives in `~/.hermes/values/graph.json` |

### Why Not Just USER.md?

USER.md has a 1,375-character cap and uses a frozen-snapshot pattern (loaded at
session start, not updated mid-session). It's the right **surface** but the
wrong **substrate**:

- A flat file can't represent a moral graph (edges, PageRank, confidence scores)
- You can't run deduplication without structured data and embeddings
- Context window pressure grows linearly; a graph backend serves only what's relevant

The full graph lives in `~/.hermes/values/graph.json`. USER.md gets a curated
summary — the graph is the substrate, the markdown is the surface.

### Data Flow

```
User says something meaningful
        │
        ▼
SKILL.md teaches Hermes to notice ──────── 5 signals:
        │                                  affect, choice, admiration,
        ▼                                  resistance, aspiration
Hermes invokes: values extract
        │
        ▼
extract_value.md ─── LLM ──► Value or None
        │
        ▼ (if found)
check_duplicate.md ── LLM ──► duplicate_of or None
        │
        ▼ (if new)
graph.json ◄── add_value() ── recompute PageRank
        │
        ▼
detect_upgrade.md ── LLM ──► Edge + Upgrade narratives
        │
        ▼
graph.json ◄── add_edge() + add_upgrade()
        │
        ▼
render_user_summary.md ── LLM ──► prose portrait
        │
        ▼
USER.md ◄── inject between markers
```

### Deduplication (5 Criteria)

Two values are duplicates if and only if ALL FIVE hold:

1. **Completeness** — every policy in the new value has a correspondent
2. **Practical equivalence** — both attend to the same things in practice
3. **Design alignment** — both lead to the same choices
4. **Mutual correction** — deviation from one is corrected by the other
5. **Granularity consistency** — same level of specificity

Partial overlap with genuinely new attention policies is NOT a duplicate.

## Install

```bash
# One-liner
curl -fsSL https://raw.githubusercontent.com/withdhyan/meaning-maxxing/main/install.sh | bash

# Or from a clone
git clone https://github.com/withdhyan/meaning-maxxing.git
cd meaning-maxxing
./install.sh
```

This copies the skill into `~/.hermes/skills/value-extraction/` and creates
`~/.hermes/values/` for graph storage.

## Tool Actions

| Action | Trigger | What it does |
|--------|---------|-------------|
| `values extract` | Agent notices a value-laden moment | Runs full pipeline: extract -> dedup -> upgrade -> render |
| `values show` | Agent needs to understand the user | Displays moral graph with ranked values and growth |
| `values upgrades` | Agent wants to show growth | Lists upgrade narratives between values |
| `values remove` | User disowns a value | Removes value and cascades edge/upgrade cleanup |
| `values tws` | Agent or user wants the wisdom score | Computes and displays depth/growth/coherence/TWS |

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

91 tests covering types, extraction, storage, rendering, and tool orchestration.

## Lineage

- **[Democratic Fine-Tuning](https://meaningalignment.org)** (Meaning Alignment Institute) —
  the methodology: values as attention policies, moral graphs, wiser-than relationships,
  upgrade narratives. Funded by OpenAI.
- **[values-tools](https://github.com/meaningalignment/values-tools)** (MAI) —
  the TypeScript library implementing articulation, deduplication, and graph construction.
  We reimplement the core ideas in Python, adapted for the Hermes runtime.
- **[Hermes Agent](https://github.com/NousResearch/hermes-agent)** (Nous Research) —
  the agent framework: skill system, tool registry, USER.md/MEMORY.md persistence,
  multi-platform messaging, self-improving learning loop.

## License

GPL-3.0
