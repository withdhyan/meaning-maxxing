# meaning-maxxing

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) skill that
extracts your deeply held values from conversation and writes them to USER.md.

Built on the [Meaning Alignment Institute](https://meaningalignment.org)'s
[value-tools](https://github.com/meaningalignment/values-tools) methodology.

## What It Does

As you talk to Hermes, the agent notices when something matters to you — a
difficult choice, something that moved you, a person you admire, a suggestion
you push back on. It silently extracts **sources of meaning** and writes them
to your profile.

Values are expressed as **attention policies** — the MAI's core primitive:

> **Generative Honesty**
> - MOMENTS where telling a difficult truth opens a new possibility
> - SIGNS that someone is ready to hear what they need to hear
> - WAYS of speaking that make hard truths land as gifts rather than weapons

These aren't preferences ("I like dark mode") or goals ("I want a promotion").
They're descriptions of what you actually attend to when something matters.

## Time Well Spent

The design principle: this is time well spent — not because it optimizes
anything, but because understanding what matters to someone is how you
actually help them.

The agent is present, not extractive. It doesn't interview you about your
values. It notices them as a byproduct of genuine engagement. You should
feel understood, not studied.

## Architecture

```
skill/
├── SKILL.md                    # Teaches Hermes the methodology
├── prompts/
│   └── extract_value.md        # Value articulation prompt
└── scripts/
    ├── __init__.py
    └── values.py               # Everything: storage, extraction, USER.md
tests/
└── test_values.py              # 25 tests
install.sh                      # One-command install
```

One file does it all. `values.py` handles:
- **Storage**: values as a JSON list in `~/.hermes/values/values.json`
- **Extraction**: LLM message building + JSON response parsing
- **USER.md**: marker-delimited section injection (`<!-- values-start/end -->`)
- **Display**: human-readable value listing

## How It Works

```
User says something meaningful
        │
        ▼
SKILL.md teaches Hermes to notice ── 5 signals:
        │                             affect, choice, admiration,
        ▼                             resistance, aspiration
values extract (with context)
        │
        ▼
extract_value.md ── LLM ──► value or nothing
        │
        ▼
values.json ◄── append
        │
        ▼
USER.md ◄── write between markers
```

## Install

```bash
# One-liner
curl -fsSL https://raw.githubusercontent.com/withdhyan/meaning-maxxing/main/install.sh | bash

# Or from a clone
git clone https://github.com/withdhyan/meaning-maxxing.git
cd meaning-maxxing
./install.sh
```

## What Lands in USER.md

```markdown
<!-- values-start -->
**Generative Honesty**: MOMENTS where telling a difficult truth opens a new
possibility; SIGNS that someone is ready to hear what they need to hear; WAYS
of speaking that make hard truths land as gifts rather than weapons
**Quiet Stewardship**: MOMENTS where care is given without being asked; SIGNS
that something fragile is being tended; WAYS of nurturing that don't need
acknowledgment
<!-- values-end -->
```

This section is preserved across updates. Existing USER.md content outside the
markers is untouched.

## Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Lineage

- **[Democratic Fine-Tuning](https://meaningalignment.org)** (MAI) — values as
  attention policies, funded by OpenAI
- **[values-tools](https://github.com/meaningalignment/values-tools)** (MAI) —
  TypeScript library we draw methodology from
- **[Hermes Agent](https://github.com/NousResearch/hermes-agent)** (Nous Research) —
  the agent framework

## License

GPL-3.0
