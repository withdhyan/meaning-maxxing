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
skill/                              # Hermes Agent skill (individual)
├── SKILL.md                        # Teaches Hermes the methodology + alignment
├── prompts/
│   └── extract_value.md            # Value articulation prompt (grading + dedup)
├── references/
│   └── LINEAGE.md                  # MAI philosophy, papers, concepts, results
└── scripts/
    ├── __init__.py
    └── values.py                   # Extraction, storage, emission, USER.md

matching/                           # Social matching engine (collective)
├── __init__.py
├── store.py                        # SQLite: canonical values + user-value links
├── dedup.py                        # Policy similarity + deduplication
├── matcher.py                      # Find aligned users by shared values
└── app.py                          # FastAPI: /emit, /match, /values, /user

tests/
├── test_values.py                  # 37 skill tests
└── test_matching.py                # 35 matching tests
```

Two systems, one methodology:

**Skill** — individual. Extracts values from one user's conversation, writes to
USER.md so Hermes can align to what matters to them.

**Matching engine** — collective. Hermes agents emit anonymized values to a
shared graph. Users are matched by shared sources of meaning.

## How It Works

### Individual: extract and align

```
User says something meaningful
        │
        ▼
SKILL.md teaches Hermes to notice ── 5 signals:
        │                             affect, choice, admiration,
        ▼                             resistance, aspiration
values extract (with context + existing values for dedup)
        │
        ▼
extract_value.md ── LLM ──► value or nothing
        │
        ▼
values.json ◄── append (deduplicated)
        │
        ▼
USER.md ◄── write between markers
        │
        ▼
Hermes reads USER.md ── alignment shapes responses
```

### Collective: emit and match

```
Hermes A        Hermes B        Hermes C
values.json     values.json     values.json
    │               │               │
    ▼ anonymize     ▼               ▼
    └───────┐   ┌───┘   ┌──────────┘
            ▼   ▼       ▼
       POST /emit (with consent)
                │
                ▼
       Canonical Value Graph  ◄── dedup collapses
       (SQLite)                   similar values
                │
                ▼
       GET /match/{user_id}
                │
                ▼
       shared: [Quiet Stewardship]
       alignment: 0.67
       resonance: 0.31
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

## Matching API

```bash
pip install -r requirements.txt
uvicorn matching.app:app --reload
```

Endpoints:
- `POST /emit` — agent publishes anonymized values
- `GET /match/{user_id}` — find most aligned users
- `GET /values` — all canonical values in the graph
- `GET /user/{user_id}` — a user's canonical values

## Tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v   # 72 tests
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
