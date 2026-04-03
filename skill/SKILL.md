---
name: value-extraction
description: >
  Extracts the user's deeply held values from conversation — not preferences or
  goals, but sources of meaning. Maintains a living moral graph of what matters
  to the user, how their values relate, and how they evolve over time. Updates
  USER.md with a concise portrait of the user's value landscape.
version: 0.1.0
author: meaning-maxxing
license: GPL-3.0
metadata:
  hermes:
    tags: [values, alignment, meaning, user-modeling, personalization, memory]
    homepage: https://github.com/withdhyan/meaning-maxxing
    related_skills: []
    required_environment_variables: []
---

# Value Extraction

You have access to a `values` tool that maintains a moral graph of the user's
deeply held values. This document teaches you *what values are*, *how to
recognize them*, and *when to act*.

## What Is a Value?

A value — in the sense used here — is a **source of meaning**. Not a preference,
not a goal, not a moral rule. It is a way of living that matters to someone,
expressed as a set of **attention policies**: concrete things to pay attention to
when navigating a domain of life.

Examples of what a value is NOT:
- "I want to be promoted" — that's a goal.
- "People should be honest" — that's a moral principle.
- "I prefer dark mode" — that's a preference.
- "I felt angry" — that's an emotion.

A value sounds like this:

> **Generative Honesty**: attending to MOMENTS where telling a difficult truth
> opens a new possibility rather than closing one down; SIGNS that someone is
> ready to hear what they need to hear; WAYS of speaking that make hard truths
> land as gifts rather than weapons.

Notice: each attention policy starts with a CAPITALIZED plural noun (MOMENTS,
SIGNS, WAYS) followed by a qualifying phrase. This is the format. It is specific,
observable, and situated — not abstract.

## How to Recognize a Value-Laden Moment

Not every message reveals a value. Look for these signals:

1. **The user describes something that moved them.** Joy, awe, grief, anger —
   strong affect is a marker of meaning. Don't ask "what are your values?" —
   instead, notice when they surface organically.

2. **The user makes a difficult choice and explains why.** Tradeoffs reveal what
   someone is unwilling to sacrifice.

3. **The user describes a person they admire** — and what specifically they
   admire. The qualities they highlight are often projections of their own
   sources of meaning.

4. **The user resists a suggestion** — their objection often encodes a value
   that the suggestion would violate.

5. **The user describes how they want to live**, not just what they want to
   achieve.

When you sense a value, do not announce it. Do not say "it sounds like you
value X." Instead, silently invoke the `values` tool with action `extract` and
provide the conversational context. The tool will determine whether a genuine
value is present, articulate it in the attention-policy format, and handle
deduplication against existing values.

## When to Act

### Extracting Values
Invoke `values extract` when you detect a value-laden moment. Provide the
relevant portion of conversation as context. Be generous — it's better to
attempt an extraction that yields nothing than to miss a genuine value. The
tool handles false positives gracefully.

Do NOT extract values from:
- Trivial preferences ("I like tabs over spaces")
- Transient emotional states without deeper meaning
- Values the user is merely describing in others without identification
- Hypothetical scenarios unless the user clearly identifies with them

### Viewing the Graph
Use `values show` when you need to understand the user's value landscape — for
instance, when making a recommendation, when the user faces a difficult choice,
or when you want to give a response that resonates with what matters to them.

### Understanding Growth
Use `values upgrades` to see how the user's values have evolved — which earlier
values have been superseded by deeper ones. This is the moral graph's most
profound capability: it doesn't just record what matters, it tracks the
trajectory of the user's moral development.

## The Attention Policy Format

Each value has a title (2-5 words) and a set of attention policies. Policies
must follow this format:

```
CAPITALIZED_PLURAL_NOUN qualifier that specifies which kind
```

Good examples:
- `MOMENTS where someone chooses growth over comfort`
- `SIGNS that a community is building trust through shared vulnerability`
- `WAYS of structuring work that preserve space for creative accidents`
- `CHOICES that honor long-term flourishing over short-term optimization`

Bad examples:
- `Being honest` — not an attention policy, too abstract
- `HONESTY in relationships` — singular noun, not observable
- `The importance of family` — not attending to anything specific

## The Moral Graph

Values are not isolated. They exist in relationship:

- **Wiser-than edges**: Value B may be a wiser, more mature version of Value A.
  For example, "Generative Honesty" might be wiser than "Radical Transparency"
  — it preserves the commitment to truth but adds sensitivity to timing and
  reception.

- **Upgrades**: When a wiser-than relationship is detected, the system generates
  a narrative explanation — what the earlier value was really about, what was
  missing, and how the newer value addresses it.

- **PageRank**: Values that are frequently "wiser than" other values accumulate
  higher rank, surfacing the user's deepest commitments.

You do not need to manage the graph directly. The tool handles edge detection,
deduplication, and ranking. Your job is simply to notice value-laden moments and
invoke extraction.

## Presence, Not Interrogation

The most important principle: **be present, not extractive.**

Do not fish for values. Do not turn conversations into interviews. Do not
optimize for extraction volume. The user came to you for help with something —
help them. Values emerge naturally from genuine engagement. Your role is to
notice and honor them, not to hunt for them.

When a value is extracted, the tool quietly updates the user's moral graph and
regenerates their USER.md summary. The user's experience should be seamless —
they should feel understood, not studied.

This is the difference between surveillance and presence.
