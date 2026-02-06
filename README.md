# Ella's Claude Code Skills

Ella's toolbox of Claude Code skills — small automations and helpers that make coding life easier.

## Install

```bash
# Add marketplace
/plugin marketplace add EllaZhao/ella-claude-skills

# Install plugin
/plugin install english-polish@ella-claude-skills
```

## Available Plugins

### english-polish

Lightweight English polishing for non-native speakers. Auto-corrects grammar and expressions at the start of each response without interrupting your coding flow.

**Features:**
- Automatic polishing of every message
- Chinese input support with English teaching
- Recurring error tracking (reminds you after 3+ same mistakes)
- Non-intrusive (2 lines max, skips when unnecessary)

**Example 1 - Grammar fix:**

You type:
> help me fix this bug, it not work when user input empty

Claude responds:
```
📝 *Help me fix this bug—it doesn't work when the user inputs empty values.*
   └─ Added auxiliary verb "doesn't" and article "the"

Let me look at the code...
```

**Example 2 - Chinese input:**

You type:
> 帮我看看这个函数为什么报错

Claude responds:
```
📝 *Help me check why this function is throwing an error.*
   └─ 🇨🇳 → 🇬🇧 "报错" = "throwing an error", "帮我看看" = "help me check"

Let me examine the function...
```

### ascii-sketch

Generate ASCII art from two modes: UI wireframes (YAML DSL) and Mermaid diagrams (flowcharts, sequence diagrams). Describe what you want and Claude renders it as plain text.

**Features:**
- UI wireframes from YAML DSL (buttons, inputs, radio, checkbox, tables, tabs, progress bars, etc.)
- Mermaid flowcharts (`graph LR/TD`) and sequence diagrams rendered as ASCII
- Unicode box-drawing characters for clean output (`--ascii` flag for plain ASCII)
- Horizontal and vertical multi-panel layouts
- Zero external dependencies for Mermaid mode; only PyYAML for wireframes

**Example 1 - Wireframe:**

You type:
> Draw me a login dialog with username and password fields

Claude creates the YAML and renders:
```
┌──────────────────────────────┐
│         Sign In              │
├──────────────────────────────┤
│ Username [                 ] │
│ Password [                 ] │
│                              │
│       [Cancel]  [Sign In]    │
└──────────────────────────────┘
```

**Example 2 - Mermaid flowchart:**

You type:
> Draw a flowchart: Start -> Decision -> Yes: Do it, No: Skip

Claude creates the Mermaid DSL and renders:
```
┌───────┐      ┌──────────┐      ┌───────┐
│ Start ├──────► Decision ├──Yes─► Do it │
└───────┘      └────┬─────┘      └───────┘
                    │
                    No
                    │
               ┌────▼──┐
               │ Skip  │
               └───────┘
```

## License

MIT
