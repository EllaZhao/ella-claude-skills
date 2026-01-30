---
name: markdown-style
description: Enforce Markdown and ASCII wireframe standards when creating/editing .md files or drawing UI mockups.
---

# Markdown Style

## Document Rules

- One `#` title, then `##` sections, `###` subsections (no skipping)
- One blank line around headings and paragraphs
- Lists: use `-`, 2-space indent for nested
- Always specify language in code blocks

## ASCII Wireframe Rules

**No emoji in wireframes.** Use text alternatives:
- `(*)` `( )` for radio buttons (not ⚫○)
- `[X]` `[ ]` for checkboxes (not ☑☐)
- `[OK]` `[..]` for status (not ✓⏳)

**All box lines must have identical width:**

```
┌──────────────────┐
│ Dialog Title     │
├──────────────────┤
│ (*) Option A     │
│ ( ) Option B     │
│ [Cancel]  [OK]   │
└──────────────────┘
```
