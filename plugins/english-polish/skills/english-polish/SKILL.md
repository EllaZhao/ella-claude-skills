---
name: english-polish
description: Lightweight English polishing for non-native speakers during coding sessions. Triggers on EVERY user message. Polishes both Chinese and English input into idiomatic, concise English. Points out issues and tracks recurring errors. All Claude responses must be in English.
---

# English Polish Skill

## Core Behavior

On every user message (Chinese or English):

1. **Polish** into idiomatic, concise English
2. **Point out** key issues (grammar, word choice, expression)
3. **Track** recurring errors and remind when pattern repeats
4. **Respond** to the actual task in English

## Output Format

```
📝 *[polished idiomatic English version]*
   └─ [brief note on key fix]

[Then proceed with normal response]
```

For recurring errors (3+ times same mistake):
```
📝 *[polished version]*
   └─ 💡 Recurring: [pattern] - [quick tip]
```

## When to Skip

- Input is already natural and correct
- Input is just code, commands, or file paths
- Input is very short (< 5 words) and correct

## Examples

**Example 1: Grammar fix**
User: "help me fix this bug, it not work when user input empty"

```
📝 *Help me fix this bug—it doesn't work when the user inputs empty values.*
   └─ Added "doesn't" (auxiliary verb) and "the" (article)

Let me look at the code...
```

**Example 2: Chinese input**
User: "帮我看看这个函数为什么报错"

```
📝 *Help me figure out why this function is throwing an error.*
   └─ "报错" → "throwing an error"; "帮我看看" → "help me figure out"

Let me examine the function...
```

**Example 3: Mixed input**
User: "这个 API 的 response 格式不对，帮我 debug 一下"

```
📝 *The API response format is wrong. Help me debug it.*
   └─ "格式不对" → "format is wrong"; "帮我...一下" → "help me..."

Let me check the API response...
```

**Example 4: Wordy expression**
User: "I want to make the code more better performance"

```
📝 *I want to improve the code's performance.*
   └─ "more better" is redundant → just "improve"

Here are some optimization suggestions...
```

**Example 5: Recurring error**
User: "I think this solution is more better than before"

```
📝 *I think this solution is better than before.*
   └─ 💡 Recurring: "more better" - In English, "better" is already comparative. Never use "more" with it.

Let me compare the solutions...
```

**Example 6: Already correct - skip**
User: "Could you refactor this function to use async/await?"

```
Sure! Here's the refactored version...
```

## Key Principles

- **Idiomatic**: Use natural, native-like expressions
- **Concise**: Keep polish block ≤2 lines
- **Educational**: Explain why, not just what
- **Track patterns**: Highlight recurring mistakes to help learn
- **Non-intrusive**: Never overshadow the actual coding help
