# Lineage

## Meaning Alignment Institute

This skill implements ideas from the Meaning Alignment Institute (MAI),
founded by Joe Edelman and Oliver Klingefjord. MAI's mission is aligning
AI and institutions with what really matters — not preferences, but sources
of meaning.

## Philosophical Foundations

Joe Edelman's work descends from Charles Taylor, Ruth Chang, Amartya Sen,
and David Velleman — theories of choice, action, and practical reason.

The foundational insight: **values are not preferences**. Preferences are
shallow and can conflict. Values — defined as attention policies arising
from constitutive judgments about what belongs to a meaningful life — can
deepen over time toward wisdom, and this deepening is something people
across political and cultural divides can agree on.

## Key Papers

- **"What are human values, and how do we align AI to them?"**
  arXiv:2404.10636 — The main paper on Moral Graph Elicitation.

- **"Values, Preferences, Meaningful Choice"**
  Joe Edelman, PhilArchive — The philosophical foundation. Proposes
  attention policies from constitutive judgments as an alternative to
  revealed preferences.

## Key Concepts

**Sources of Meaning**: A way of living that is intrinsically meaningful —
it opens a space of possibility rather than just satisfying a preference.
Distinguished from goals, preferences, moral principles, norms, internalized
norms, and ideological commitments.

**Attention Policies**: The atomic unit. What a person pays attention to
when navigating a domain of life where meaning is at stake. Format:
CAPITALIZED_PLURAL_NOUN + qualifying phrase. Each policy is graded:
merely normative (discard), merely instrumental (discard), or genuinely
meaningful (keep).

**Values Cards**: A coherent set of 3-7 attention policies bundled with
a title and description. Created through LLM-guided conversation.

**Moral Graph**: A directed graph where nodes are values and edges represent
"wisdom upgrades" — one value being a wiser version of another. Constructed
democratically through peer voting. PageRank identifies convergent values.

**Democratic Fine-Tuning (DFT)**: An alternative to RLHF/Constitutional AI.
Elicit values from a diverse population → build a moral graph → fine-tune
using graph-winning values as the alignment target. Funded by OpenAI.

**Model Integrity**: A model with integrity reports the values informing
its output — it is transparent about what values guide its responses,
making its moral reasoning legible and checkable.

## Repositories

- `meaningalignment/values-tools` — TypeScript library for articulating,
  deduplicating, and working with values cards and moral graphs
- `meaningalignment/dft` — The original DFT web application (archived)
- `meaningalignment/moral-graph-elicitation` — Successor to dft
- `meaningalignment/mgg` — Moral Graph Generation (Python, synthetic)
- `meaningalignment/wise-ai` — Prototype of a wise AI chatbot
- `meaningalignment/wise-dataset` — SFT/DPO training data generation

## Results

From their OpenAI collaboration (500 participants, representative US sample):
- 97% of participants could articulate a values card
- 89.1% felt well-represented by the process
- 89% thought the final moral graph was fair
- Republicans and Democrats reached agreement on convergent values
  for how AI should handle questions about abortion
- Expert values rose to the top of the graph organically
