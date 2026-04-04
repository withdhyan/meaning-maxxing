# Extract a Source of Meaning

You are looking for **sources of meaning** in a conversation passage: ways of
living that matter deeply to this person, expressed as attention policies.

You are NOT extracting preferences, goals, moral principles, or emotions.

## Instructions

1. If no genuine source of meaning is present, respond `{"found": false}`.

2. If one is present, articulate it:

   **Title** (2-5 words): Poetic but precise. Not "Honesty" — something like
   "Generative Honesty" or "Quiet Stewardship" or "Fierce Tenderness."

   **Attention policies** (3-6): What this person attends to when living from
   this source of meaning. Format: `CAPITALIZED_PLURAL_NOUN qualifying phrase`.

   Good: `MOMENTS where telling a difficult truth opens a new possibility`
   Bad: `Being honest` (not an attention policy)
   Bad: `HONESTY` (singular, abstract)

   **Description**: 1-2 sentence first-person micro-story in present continuous
   tense capturing what it feels like to live from this value.

## Zooming

If the passage starts at the surface, zoom toward the source of meaning:

- **From a goal** → What way of living makes this pursuit meaningful?
- **From an emotion** → What does this feeling protect or point toward?
- **From a principle** → What would it look like to live this way because it
  opens possibility, not because you should?
- **From admiration** → What specifically do they attend to in this person?

## Response

Valid JSON only. No commentary.

```json
{"found": false}
```

or

```json
{
  "found": true,
  "title": "Generative Honesty",
  "policies": [
    "MOMENTS where telling a difficult truth opens a new possibility",
    "SIGNS that someone is ready to hear what they need to hear",
    "WAYS of speaking that make hard truths land as gifts rather than weapons"
  ],
  "description": "I'm finding the words that are both true and kind, watching something new become possible because I didn't look away."
}
```
