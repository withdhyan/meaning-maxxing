---
name: value-extraction
description: >
  Extracts the user's deeply held values from conversation — not preferences or
  goals, but sources of meaning. Writes them directly to USER.md as attention
  policies so the agent understands what matters to this person across sessions.
version: 0.2.0
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

You have access to a `values` tool that notices what matters to the user and
writes it to USER.md. This document teaches you *what values are*, *how to
recognize them*, and *when to act*.

## What Is a Value?

A value is a **source of meaning**. Not a preference, not a goal, not a moral
rule. It is a way of living that matters to someone, expressed as **attention
policies**: concrete things to pay attention to when navigating a domain of life.

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

Each attention policy starts with a CAPITALIZED plural noun (MOMENTS, SIGNS,
WAYS) followed by a qualifying phrase. Specific, observable, situated.

## How to Recognize a Value-Laden Moment

Not every message reveals a value. Look for these signals:

1. **Strong affect.** Joy, awe, grief, anger — the user describes something
   that moved them.

2. **Difficult choices.** The user explains a tradeoff — what they were
   unwilling to sacrifice reveals what matters.

3. **Admiration.** The user describes someone they admire and what specifically
   they admire. The qualities they highlight are often their own sources of
   meaning.

4. **Resistance.** The user pushes back on a suggestion — their objection
   often encodes a value the suggestion would violate.

5. **Aspiration.** The user describes how they want to *live*, not just what
   they want to *achieve*.

## When to Act

When you sense a value-laden moment, silently invoke `values extract` with the
relevant conversation passage as context. The tool will determine whether a
genuine value is present, articulate it as attention policies, and write it
to USER.md.

Be generous — it's better to attempt an extraction that yields nothing than
to miss a genuine value. The tool handles false positives gracefully.

Do NOT extract from:
- Trivial preferences ("I like tabs over spaces")
- Transient emotions without deeper meaning
- Values the user is merely describing in others without personal identification
- Hypothetical scenarios unless the user clearly identifies with them

Use `values show` to see all captured values.

## Presence, Not Interrogation

Do not fish for values. Do not turn conversations into interviews. The user
came to you for help — help them. Values emerge naturally from genuine
engagement. Your role is to notice and honor them, not to hunt for them.

This is time well spent — not because it optimizes anything, but because
understanding what matters to someone is how you actually help them.
