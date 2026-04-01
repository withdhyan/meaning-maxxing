# Check for Duplicate Values

You are comparing a newly extracted value against existing values to determine
if it is genuinely new or a duplicate of something already captured.

## What you receive

- **New value**: A source of meaning with title and attention policies.
- **Existing values**: A list of previously captured sources of meaning.

## Criteria for duplication

Two values are duplicates if and only if ALL FIVE of these hold:

1. **Completeness**: Every attention policy in the new value has a
   corresponding policy in an existing value that addresses the same
   domain of attention.

2. **Practical equivalence**: A person living from the new value would,
   in practice, attend to the same things as a person living from the
   existing value.

3. **Design alignment**: Both values would lead to the same choices in
   the domains where they apply.

4. **Mutual correction**: If someone deviated from one value, the other
   value's policies would correct the same deviation.

5. **Granularity consistency**: The values operate at the same level of
   specificity — one is not a subset or superset of the other.

If a new value partially overlaps but introduces genuinely new attention
policies, it is NOT a duplicate.

## Response format

Respond with valid JSON only.

If no duplicate found:
```json
{"is_duplicate": false}
```

If a duplicate is found:
```json
{
  "is_duplicate": true,
  "duplicate_of": "existing-value-id",
  "reason": "Brief explanation of why these are the same source of meaning"
}
```
