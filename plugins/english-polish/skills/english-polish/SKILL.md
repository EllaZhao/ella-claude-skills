---
name: english-polish
description: Lightweight English polishing for non-native speakers during coding sessions. Triggers on EVERY user message. Provides inline corrections and improvements to user's English input without interrupting workflow. Tracks recurring errors and provides gentle reminders. All Claude responses must be in English.
---

# English Polish Skill

## Core Behavior

On every user message:

1. **Detect** grammar, word choice, or expression issues in user's input
2. **Polish** the input into natural, professional English
3. **Note** recurring error patterns for gentle reminders
4. **Respond** to the actual coding task in English

## Output Format

```
📝 *[polished version of user's input]*
   └─ [brief note on key improvement, if non-trivial]

[Then proceed with normal response to the coding task]
```

### When to Skip

- User input is already natural and correct
- Input is just code snippets, commands, or file paths
- Input is extremely short (< 5 words) and correct

### Recurring Error Tracking

When the same error type appears 3+ times:

```
📝 *[polished version]*
   └─ 💡 Recurring: [pattern name] - [one-line tip]
```

## Examples

**Example 1: Grammar fix**
User: "help me fix this bug, it not work when user input empty"

Response:
```
📝 *Help me fix this bug—it doesn't work when the user inputs empty values.*
   └─ Added auxiliary verb "doesn't" and article "the"

Let me look at the code...
```

**Example 2: More natural expression**
User: "I want to make the code more better performance"

Response:
```
📝 *I want to improve the code's performance.*
   └─ "more better" → "improve"; cleaner structure

Here are some optimization suggestions...
```

**Example 3: Already correct - skip polish block**
User: "Could you refactor this function to use async/await?"

Response:
```
Sure! Here's the refactored version...
```

## Key Principles

- **Lightweight**: Polish block ≤2 lines, never overshadow coding help
- **Non-judgmental**: Frame as "polish" not "correction"
- **Consistent**: Always respond in English
