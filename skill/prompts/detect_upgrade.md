# Detect Value Upgrades

You are examining a newly extracted value against the user's existing values
to determine if it represents moral growth — a **wiser** version of something
they already held.

## What is an upgrade?

An upgrade is NOT simply a different value. It is a specific relationship:
the new value preserves the *core concern* of an earlier value while
addressing something the earlier value missed, was confused about, or
handled less skillfully.

Three patterns of upgrade:

1. **Partial → Whole**: The earlier value addressed only part of what mattered.
   The new value addresses the full picture.

2. **Impure → Pure**: The earlier value was entangled with ego, social status,
   shame, or fear. The new value pursues the same underlying good without
   those distortions.

3. **Unskillful → Skillful**: The earlier value had the right target but
   a clumsy approach. The new value achieves the same aim more gracefully.

## What you receive

- **New value**: The recently extracted source of meaning.
- **Existing values**: The user's current value landscape.

## What you must determine

For each existing value, ask: does the new value represent a deepening of
THIS existing value? If so, produce an upgrade narrative.

Most values will NOT be upgrades of each other. Be selective. A genuine
upgrade is rare and significant.

## Response format

Respond with valid JSON only.

```json
{
  "upgrades": [
    {
      "source_id": "id-of-earlier-value",
      "clarification": "What the earlier value was really about — the kernel of genuine concern underneath its limitations.",
      "story": "A first-person narrative (2-3 sentences) of how someone might grow from the earlier value to the new one. Written with tenderness toward the earlier self. No PII.",
      "mapping": [
        {
          "old_policy": "The earlier attention policy",
          "new_understanding": "How this concern is addressed more wisely in the new value"
        }
      ],
      "likelihood": "A-F grade. A = clearly an upgrade. C = plausible. F = unlikely."
    }
  ]
}
```

If no upgrades are detected:
```json
{"upgrades": []}
```
