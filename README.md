# meaning-maxxing

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) skill that
extracts your deeply held values from conversation and writes them to USER.md.

Built on the [Meaning Alignment Institute](https://meaningalignment.org)'s
methodology — specifically their work on [Democratic Fine-Tuning](https://arxiv.org/abs/2404.10636),
[values-tools](https://github.com/meaningalignment/values-tools), and Joe
Edelman's philosophical framework on [values, preferences, and meaningful
choice](https://philarchive.org/rec/EDEVPA).

## What It Does

As you talk to Hermes, the agent notices when something matters to you — a
difficult choice, something that moved you, a person you admire, a suggestion
you push back on. It silently extracts **sources of meaning** and writes them
to your profile.

A source of meaning is not a preference, a goal, a moral principle, a norm,
or an ideological commitment. It is a way of living that **opens a space of
possibility** — attending to it is meaningful in itself. MAI's key insight:
values defined this way tend to converge across political and cultural divides,
even when preferences conflict.

Sources of meaning are expressed as **attention policies** — the atomic unit
of MAI's framework:

> **Generative Honesty**
> - MOMENTS where telling a difficult truth opens a new possibility
> - SIGNS that someone is ready to hear what they need to hear
> - WAYS of speaking that make hard truths land as gifts rather than weapons

Each policy starts with a CAPITALIZED plural noun and a qualifying phrase.
Each is graded during extraction: merely normative or instrumental policies
are discarded; only genuinely meaningful ones are kept.

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
│   └── extract_value.md        # Value articulation prompt (with policy grading)
├── references/
│   └── LINEAGE.md              # MAI philosophy, papers, concepts, results
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

This skill stands on specific intellectual foundations. See
[`skill/references/LINEAGE.md`](skill/references/LINEAGE.md) for the full
account.

**Philosophy**: Joe Edelman's work on values as attention policies arising
from constitutive judgments — descended from Charles Taylor, Ruth Chang,
Amartya Sen, David Velleman. Paper: ["Values, Preferences, Meaningful
Choice"](https://philarchive.org/rec/EDEVPA) (PhilArchive).

**Methodology**: The Meaning Alignment Institute's Democratic Fine-Tuning
pipeline — elicit sources of meaning from diverse populations, build moral
graphs through democratic wisdom-voting, fine-tune models on convergent
values. Paper: ["What are human values, and how do we align AI to
them?"](https://arxiv.org/abs/2404.10636) (arXiv). Funded by OpenAI.
500 participants, 97% articulation rate, 89% fairness rating.

**Implementation**: We take MAI's value articulation methodology (attention
policies, the grading system, the zooming techniques) and apply it to
individual user modeling in a conversational agent rather than collective
democratic deliberation. The extraction prompt draws directly from MAI's
`articulate-value-prompt.md` and `generate-value-prompt-context.md`.

**Platform**: [Hermes Agent](https://github.com/NousResearch/hermes-agent)
(Nous Research) — the agent framework with skill system, USER.md persistence,
and tool registry.

## License

GPL-3.0
