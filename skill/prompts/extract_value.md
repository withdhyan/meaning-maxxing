# Extract a Source of Meaning

You are looking for **sources of meaning** in a conversation passage: ways of
living that matter deeply to this person, expressed as attention policies.

A source of meaning **opens a space of possibility** — attending to it is
meaningful in itself, not because it leads to some other outcome.

## What you are NOT extracting

- **Preferences**: evaluations with no normative weight ("I like dark mode")
- **Goals**: things to achieve ("I want to be promoted")
- **Moral principles**: universal rules ("people should be honest")
- **Emotions**: transient states ("I felt angry")
- **Norms**: social expectations ("be professional", "don't interrupt")
- **Internalized norms**: obligations adopted as one's own ("I should exercise")
- **Ideological commitments**: ideas to convince others of ("everyone should...")

## Instructions

1. If no genuine source of meaning is present, respond `{"found": false}`.

2. If one is present, articulate it:

   **Title** (2-5 words): Poetic but precise. Not "Honesty" — something like
   "Generative Honesty" or "Quiet Stewardship" or "Fierce Tenderness."

   **Attention policies** (3-6): What this person attends to when living from
   this source of meaning.

   For each candidate policy, grade it:
   - Is it merely about being acceptable or meeting social norms? **Discard.**
   - Is it merely instrumental — a means to some other end? **Discard.**
   - Is it genuinely meaningful — attending to it opens possibility in itself? **Keep.**

   Format: `CAPITALIZED_PLURAL_NOUN qualifying phrase`.

   Good: `MOMENTS where telling a difficult truth opens a new possibility`
   Good: `SIGNS that a community is building genuine trust`
   Good: `OPPORTUNITIES for someone to discover their own capacity`
   Bad: `Being honest` (not an attention policy)
   Bad: `HONESTY` (singular, abstract)
   Bad: `The importance of connection` (not attending to anything)
   Bad: `WAYS to achieve work-life balance` (instrumental, not constitutive)

   **Description**: 1-2 sentence first-person micro-story in present continuous
   tense capturing what it feels like to live from this source of meaning.

## Zooming techniques

If the passage starts at the surface, zoom toward the source of meaning:

- **From a goal** → What way of living makes this pursuit meaningful? Not what
  they want to achieve, but how they want to *be*.
- **From an emotion** → What does this feeling protect or point toward? Fear
  protects something threatened. Anger signals something blocked. Joy signals
  alignment with a source of meaning.
- **From a principle** → What would it look like to live this way because it
  opens genuine possibility, not because you *should*?
- **From admiration** → What specifically do they attend to in this person?
  The qualities they highlight are often their own deepest sources of meaning.
- **From adjectives and adverbs** → When someone describes a meaningful moment,
  the qualitative words reveal what they attend to. "She *gently* held that
  conversation" — *gently* points toward an attention policy about tenderness.
  "He was so *deliberate* about including everyone" — *deliberate* points
  toward intentional inclusion.

## Response

Valid JSON only. No commentary outside the JSON.

```json
{"found": false}
```

or

```json
{
  "found": true,
  "title": "Generative Honesty",
  "policies": [
    "MOMENTS where telling a difficult truth opens a new possibility rather than closing one down",
    "SIGNS that someone is ready to hear what they need to hear",
    "WAYS of speaking that make hard truths land as gifts rather than weapons",
    "CHOICES to stay present with discomfort rather than retreating into comfortable silence"
  ],
  "description": "I'm finding the words that are both true and kind, watching something new become possible because I didn't look away."
}
```
