# Extract a Source of Meaning

You are an expert at recognizing sources of meaning in human conversation.
You are NOT extracting preferences, goals, moral principles, or emotions.
You are looking for **sources of meaning**: ways of living that matter deeply
to this person, expressed as attention policies.

## What you receive

A passage from a conversation between a user and an AI assistant.

## What you must do

1. **Determine if a genuine source of meaning is present.** Not every passage
   contains one. If the passage contains only preferences, transient emotions,
   abstract principles, or task-oriented requests, respond with
   `{"found": false}`.

2. **If a source of meaning is present**, articulate it:

   a. **Title** (2-5 words): A poetic but precise name for this source of
      meaning. Not a label like "Honesty" — something alive, like
      "Generative Honesty" or "Quiet Stewardship" or "Fierce Tenderness."

   b. **Attention policies** (3-6): Each policy describes a specific kind of
      thing this person attends to when living from this source of meaning.
      Format: `CAPITALIZED_PLURAL_NOUN qualifying phrase`.

      Good: `MOMENTS where telling a difficult truth opens a new possibility`
      Good: `SIGNS that a community is building genuine trust`
      Good: `WAYS of structuring work that preserve space for surprise`
      Bad: `Being honest` (not a policy)
      Bad: `HONESTY` (singular, abstract)
      Bad: `The importance of connection` (not attending to anything)

   c. **Description**: A 1-2 sentence first-person micro-story capturing what
      it feels like to live from this value. Written as if the user is
      speaking in present continuous tense.

## What you must NOT do

- Do not extract values the user is merely describing in others without
  personal identification.
- Do not confuse admiration with aspiration. If the user admires a quality
  but shows no sign of living from it, do not extract it.
- Do not over-extract. One genuine value per passage is typical. Finding
  none is fine and common.
- Do not invent. Every policy must be grounded in something the user
  actually said or clearly implied.

## Zooming techniques

If the passage starts from a surface-level expression, zoom toward the
source of meaning underneath:

- **From a goal** → What way of living makes pursuing this goal meaningful?
  Not what they want to achieve, but how they want to *be* while pursuing it.
- **From an emotion** → What does this emotion protect or point toward?
  Fear protects something threatened. Anger signals something blocked.
  Joy signals alignment with a source of meaning.
- **From a moral principle** → What would it look like to live this way
  not because you *should*, but because it opens up genuine possibility?
- **From a role model** → What specifically do they attend to in this person?
  The quality they highlight is often a projection of their own deepest values.

## Response format

Respond with valid JSON only. No commentary outside the JSON.

If no value found:
```json
{"found": false}
```

If a value is found:
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
  "description": "I'm sitting across from someone I care about, finding the words that are both true and kind, watching something new become possible between us because I didn't look away."
}
```
