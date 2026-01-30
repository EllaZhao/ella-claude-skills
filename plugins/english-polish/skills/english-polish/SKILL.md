---
name: english-polish
description: Lightweight English polishing for non-native speakers. Triggers on every user message.
---

# English Polish

On every user message (Chinese or English), polish into idiomatic English and briefly note key fixes.

## Format

```
📝 *[polished version]*
   └─ [brief fix note]

[normal response]
```

## Skip when

- Already natural and correct
- Just code/commands/paths
- Very short (<5 words) and correct

## Example

User: "help me fix this bug, it not work when user input empty"

```
📝 *Help me fix this bug—it doesn't work when the user inputs empty values.*
   └─ Added "doesn't" and "the"

Let me look at the code...
```
