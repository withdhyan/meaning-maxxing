# meaning-maxxing

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) skill that
extracts your deeply held values from conversation and maintains a living
moral graph of what matters to you.

Built on ideas from the [Meaning Alignment Institute](https://meaningalignment.org)'s
[value-tools](https://github.com/meaningalignment/values-tools) and their
Democratic Fine-Tuning research.

## What it does

As you use Hermes, the agent notices value-laden moments — when you describe
something that moved you, make a difficult choice, talk about someone you
admire, or resist a suggestion. It silently extracts **sources of meaning**:
not preferences or goals, but the specific things you attend to when something
matters.

These are expressed as **attention policies**:

> **Generative Honesty**
> - MOMENTS where telling a difficult truth opens a new possibility
> - SIGNS that someone is ready to hear what they need to hear
> - WAYS of speaking that make hard truths land as gifts rather than weapons

Values accumulate into a **moral graph** with wiser-than relationships,
PageRank scoring, and growth narratives. Your top values are rendered into
a concise summary in USER.md, giving Hermes a deepening understanding of
who you are across sessions.

## Architecture

```
skill/
├── SKILL.md                    # Skill definition — teaches Hermes the methodology
├── prompts/
│   ├── extract_value.md        # Value articulation prompt
│   ├── check_duplicate.md      # Deduplication prompt
│   ├── detect_upgrade.md       # Moral growth detection prompt
│   └── render_user_summary.md  # USER.md rendering prompt
└── scripts/
    ├── __init__.py
    ├── types.py                # Value, Edge, Upgrade, MoralGraph
    ├── extractor.py            # LLM message builders + response parsers
    ├── store.py                # JSON-backed graph persistence + PageRank
    ├── renderer.py             # USER.md injection
    ├── tool.py                 # Tool orchestrator (extract/show/upgrades/remove)
    └── register.py             # Hermes ToolRegistry bridge
```

Three layers:

| Layer | Primitive | Role |
|-------|-----------|------|
| Knowledge | `SKILL.md` | Teaches Hermes *when and why* to extract values |
| Execution | `tool.py` | Runs extraction, dedup, graph ops, USER.md rendering |
| Surface | `USER.md` | Concise portrait of the user's value landscape |

The full moral graph lives in `~/.hermes/values/graph.json`. USER.md gets
a curated summary — the graph is the substrate, the markdown is the surface.

## Install

```bash
# One-liner
curl -fsSL https://raw.githubusercontent.com/withdhyan/meaning-maxxing/main/install.sh | bash

# Or from a clone
git clone https://github.com/withdhyan/meaning-maxxing.git
cd meaning-maxxing
./install.sh
```

## How it works

1. **You talk to Hermes.** About anything. Work, life, a hard decision.

2. **Hermes notices.** The SKILL.md teaches it to recognize five signals:
   strong affect, difficult choices, admiration, resistance, and aspirational
   language.

3. **Silent extraction.** Hermes invokes `values extract` with the relevant
   passage. The extraction prompt articulates attention policies using the
   MAI methodology — zooming from surface expressions to sources of meaning.

4. **Deduplication.** New values are checked against existing ones using five
   strict criteria (completeness, practical equivalence, design alignment,
   mutual correction, granularity consistency).

5. **Upgrade detection.** The system checks if the new value is a *wiser*
   version of an existing one — partial→whole, impure→pure, or
   unskillful→skillful growth.

6. **Graph mutation.** Values, edges, and upgrade narratives are persisted.
   PageRank re-scores the graph.

7. **USER.md rendering.** A concise prose portrait of the top values is
   injected into USER.md between `<!-- values-start -->` and
   `<!-- values-end -->` markers.

## Presence, not interrogation

The most important design principle: the agent is present, not extractive.
It doesn't interview you about your values. It doesn't optimize for
extraction volume. It notices what matters as a natural byproduct of
genuine engagement.

The difference between surveillance and presence.

## License

GPL-3.0
