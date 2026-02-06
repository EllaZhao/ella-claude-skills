---
name: ascii-sketch
description: Generate ASCII art from two modes - (1) UI wireframes from YAML DSL with components like buttons, inputs, checkboxes, radio buttons, tables, tabs, and progress bars, and (2) Mermaid diagrams (flowchart LR/TD and sequence diagrams) rendered as ASCII box-drawing art. Use when the user asks to create terminal/text-based UI mockups, wireframes, TUI layouts, dialog boxes, ASCII interface sketches, or to render Mermaid diagrams as plain text. Triggers on mentions of "wireframe", "ASCII UI", "TUI mockup", "text UI", "dialog wireframe", "mermaid", "flowchart", "sequence diagram", "box drawing", or requests to visualize interfaces/diagrams in plain text. No external dependencies beyond Python 3.10+ and PyYAML.
---

# ASCII Sketch Skill

Two rendering modes via `sketch.py` (unified entry point, located in the plugin root directory):

```bash
python sketch.py input.yaml              # wireframe (auto-detect)
python sketch.py flow.mermaid             # mermaid (auto-detect)
python sketch.py input.txt --mermaid      # force mermaid mode
python sketch.py input.txt --wireframe    # force wireframe mode
echo "graph LR; A-->B" | python sketch.py - --mermaid
```

Or use the individual scripts directly:
```bash
python wireframe.py dialog.yaml           # wireframe only
python mermaid_render.py flow.mermaid      # mermaid only
python mermaid_render.py flow.mermaid --ascii  # pure ASCII (no Unicode)
```

Dependency: `pip install pyyaml` (wireframe mode only; mermaid mode is zero-dependency).

---

## Mode 1: UI Wireframes (YAML DSL)

### Single Panel

```yaml
title: "Dialog Title"
width: 40
padding: 1
components:
  - type: text
    text: "Hello"
    align: center        # left|center|right
  - type: radio
    text: "Option A"
    selected: true       # (*) vs ( )
  - type: checkbox
    text: "Enable"
    checked: true        # [X] vs [ ]
  - type: button
    text: "OK"
  - type: button_row
    options: ["Cancel", "Save"]
  - type: input
    label: "Email"
    options: ["placeholder"]
  - type: input
    label: "Name"
    options: ["value"]
    align: inline            # Label [value___] on one line
  - type: select
    options: ["Choice 1"]
    width: 20
  - type: divider        # ├──────┤
  - type: separator      # ────────
  - type: spacer         # blank line
  - type: progress
    text: "Loading"
    width: 70            # percentage
  - type: tabs
    items: ["Tab1", "Tab2"]
    active: 0
  - type: table
    columns: ["Name", "Value"]
    rows: [["k1", "v1"]]
```

### Multi-Panel

```yaml
layout: horizontal   # or vertical (default)
panels:
  - title: "Left"
    width: 25
    components: [...]
  - title: "Right"
    width: 40
    components: [...]
```

### Component Quick Reference

| Type       | Renders as                       |
|------------|----------------------------------|
| text       | Plain text with alignment        |
| radio      | `(*) Sel` / `( ) Unsel`         |
| checkbox   | `[X] On` / `[ ] Off`            |
| button     | `[Text]`                         |
| button_row | `[Cancel]  [OK]`                 |
| input      | Label + `[placeholder___]`       |
| input (inline) | `Label [placeholder___]` (align: inline) |
| select     | `[Value          ▼]`             |
| divider    | `├──────────────────┤`           |
| separator  | `──────────────────`             |
| spacer     | empty line                       |
| progress   | `[███████░░░]`                   |
| tabs       | `[Active]  Tab2  Tab3`           |
| table      | columns with `│` separators      |

---

## Mode 2: Mermaid Diagrams

### Supported Diagram Types

**Flowcharts** — `graph LR`, `graph TD`, `graph TB`, `graph RL`, `flowchart LR/TD`

```
graph LR
    A[Start] --> B{Decision}
    B -->|Yes| C[Do it]
    B -->|No| D[Skip]
```

Node shapes: `A[rect]`, `A(round)`, `A{diamond}`, `A([stadium])`

Edge styles: `-->` solid arrow, `---` line, `-.->` dotted, `==>` thick, `-->|label|` labeled

Fan-out: `A --> B & C`  Fan-in: `A & B --> C`  Chaining: `A --> B --> C`

**Sequence Diagrams** — `sequenceDiagram`

```
sequenceDiagram
    Alice->>Bob: Hello!
    Bob-->>Alice: Hi!
```

Arrow styles: `->>` solid, `-->>` dashed

### Rendering Notes

- Flowcharts use topological layering for node placement
- Straight edges render cleanly with `├──►│` connectors
- L-shaped edges use bottom-exit routing for cross-layer connections
- Use `--ascii` flag for pure ASCII (no Unicode box-drawing)

---

## Important Rules

### English Only

**All text in wireframes and diagrams MUST be English only.** This includes titles, labels, button text, placeholder text, node labels, and edge labels. Non-ASCII content (CJK, emoji, accented characters) has inconsistent display widths across terminals, editors, and chat interfaces, causing box-drawing lines to misalign.

If the user provides requirements in another language, translate all UI text to English before generating the YAML/Mermaid DSL.

**No emoji.** Use ASCII alternatives:

| Instead of | Use |
|------------|-----|
| emoji icons | `[X]` `[ ]` `(*)` `( )` |
| emoji status | `[OK]` `[FAIL]` `[...]` |
| emoji arrows | `[>]` `[<]` `[^]` `[v]` |
| emoji symbols | `[+]` `[-]` `[*]` `[!]` |

### Layout Alignment

The tool supports one level of layout: either all-vertical or all-horizontal panels. For complex UIs with mixed layouts (e.g., full-width top + two-column bottom), render each section as a **separate YAML file** and compose the outputs. Ensure total widths match:

```
Top panel:    width = W
Bottom pair:  left.width + 2 (gap) + right.width = W
```

When using horizontal layout, the tool auto-pads the shorter panel with blank lines so both panels share the same height. To get a clean result, design both panels to have similar content length.

### Wireframe Width Guidelines

- **Default width: 80** for full-app or full-window wireframes (standard terminal).
- **Small dialogs/panels: 40-55** is fine.
- **Before choosing width**: measure your longest content line, add 4 (2 borders + 2 padding). If it exceeds the chosen width the tool will silently wrap — always verify the output has no unintended line breaks.

---

## Workflow

1. Determine what the user wants: UI wireframe or Mermaid diagram
2. Write the appropriate DSL (YAML for wireframes, Mermaid for diagrams)
3. Run `python sketch.py <file>` to render
4. Show ASCII output to the user
5. Iterate: adjust width, spacing, components as needed
