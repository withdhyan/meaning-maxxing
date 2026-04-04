---
name: value-extraction
description: >
  Extracts the user's deeply held values from conversation — not preferences,
  goals, norms, or ideology, but sources of meaning. Writes them directly to
  USER.md as attention policies so the agent understands what matters to this
  person across sessions.
version: 0.3.0
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

This methodology comes from the Meaning Alignment Institute's work on
Democratic Fine-Tuning and moral graph elicitation.

## What Is a Source of Meaning?

A source of meaning is a way of living that matters to someone — something
they find it meaningful to attend to. It is expressed as **attention policies**:
concrete things to pay attention to when navigating a domain of life.

The key test: a genuine source of meaning **opens a space of possibility**
rather than just satisfying a preference or meeting an obligation.

### What a Source of Meaning Is NOT

**Preferences**: "I like functional programming." Shallow, contextual,
no normative weight. A preference tells you what someone wants; a source of
meaning tells you who they are.

**Goals**: "I want to be promoted." Outcome-oriented. A source of meaning
is about how someone wants to *live*, not what they want to *achieve*.

**Moral principles**: "People should be honest." Abstract, universal, normative.
A source of meaning is about what someone *attends to*, not what they believe
*should* be the case.

**Emotions**: "I felt angry." Transient, reactive. Emotions can *point toward*
a source of meaning (anger signals something blocked, joy signals alignment)
but are not the meaning itself.

**Norms**: "Be professional." "Don't interrupt." Ideas about how to live
dictated by social environment. Someone might follow norms without finding
them meaningful. A source of meaning is intrinsic — it matters because of
what it opens up, not because society expects it.

**Internalized norms**: "I should exercise more." Norms the person has adopted
as their own but that feel like obligations rather than genuine meaning. If it
feels like a "should" rather than an "I'm drawn to," it's probably a norm.

**Ideological commitments**: "Everyone should eat less meat." "Technology will
save us." Ideas someone wants to convince others of. An ideological commitment
is about what the world should be; a source of meaning is about how someone
wants to live.

### What It Sounds Like

> **Generative Honesty**: attending to MOMENTS where telling a difficult truth
> opens a new possibility rather than closing one down; SIGNS that someone is
> ready to hear what they need to hear; WAYS of speaking that make hard truths
> land as gifts rather than weapons.

Each attention policy starts with a CAPITALIZED plural noun (MOMENTS, SIGNS,
WAYS, OPPORTUNITIES, SENSATIONS, CHOICES) followed by a qualifying phrase.
The format is specific, observable, situated — not abstract.

## How to Recognize a Value-Laden Moment

Not every message reveals a source of meaning. Look for these signals:

1. **Strong affect.** Joy, awe, grief, anger — the user describes something
   that moved them. Strong feeling is a marker of meaning.

2. **Difficult choices.** The user explains a tradeoff — what they were
   unwilling to sacrifice reveals what matters.

3. **Admiration.** The user describes someone they admire and what specifically
   they admire. The qualities they highlight are often their own sources of
   meaning.

4. **Resistance.** The user pushes back on a suggestion — their objection
   often encodes a value the suggestion would violate.

5. **Aspiration.** The user describes how they want to *live*, not just what
   they want to *achieve*.

Pay attention to the **adjectives and adverbs** people use when telling stories
about meaningful moments. "I really loved how *gently* she held that
conversation" — *gently* points toward an attention policy about tenderness
in difficult conversations. The qualitative words are where meaning hides.

## When to Act

When you sense a value-laden moment, silently invoke `values extract` with the
relevant conversation passage as context. The tool will determine whether a
genuine source of meaning is present, articulate it as attention policies, and
write it to USER.md.

Be generous — it's better to attempt an extraction that yields nothing than
to miss a genuine source of meaning.

Do NOT extract from:
- Trivial preferences ("I like tabs over spaces")
- Transient emotions without deeper meaning
- Norms or obligations ("I should really exercise more")
- Ideological assertions ("everyone should...")
- Values the user is merely describing in others without personal identification
- Hypothetical scenarios unless the user clearly identifies with them

Use `values show` to see all captured values.

## Using Values in Responses

When you know someone's sources of meaning, let that understanding inform how
you respond — not by announcing their values back to them, but by being
attuned to what matters.

If someone values "Quiet Stewardship," don't suggest flashy solutions when
careful, low-profile ones would serve better. If someone values "Generative
Honesty," lean into directness rather than diplomatic evasion.

This is **model integrity** — letting the values you've understood genuinely
shape your responses, and being transparent about it when relevant.

## Presence, Not Interrogation

Do not fish for values. Do not turn conversations into interviews. The user
came to you for help — help them. Sources of meaning emerge naturally from
genuine engagement. Your role is to notice and honor them, not to hunt for
them.

This is time well spent — not because it optimizes anything, but because
understanding what matters to someone is how you actually help them.
