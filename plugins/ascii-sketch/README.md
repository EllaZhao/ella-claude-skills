# ascii-sketch: Claude Code Setup Guide

## Step 1: Place the Skill Files

Choose an installation scope:

```bash
# Option A: Global install (available to all projects)
cp -r ascii-sketch ~/.claude/skills/ascii-sketch

# Option B: Project-level install (current project only)
cp -r ascii-sketch .claude/skills/ascii-sketch
```

## Step 2: Add Usage Policy to CLAUDE.md

This is the key step. The `description` field in SKILL.md determines when the skill gets "activated", but CLAUDE.md is the project-level instruction file that Claude Code reads at the start of every conversation. Adding a diagram policy here ensures automatic triggering.

Add the following to your project's `CLAUDE.md` (create one if it doesn't exist):

```markdown
## Diagram & Wireframe Policy

When writing Markdown files that need diagrams (flowcharts, sequence diagrams,
architecture diagrams, UI wireframes), use the `ascii-sketch` skill instead of
Mermaid code blocks:

- For flowcharts/sequence diagrams: write a `.mermaid` file, run
  `python ~/.claude/skills/ascii-sketch/mermaid_render.py <file>`
  and paste the ASCII output into the Markdown as a code block.
- For UI wireframes/dialog mockups: write a `.yaml` file, run
  `python ~/.claude/skills/ascii-sketch/wireframe.py <file>`
  and paste the ASCII output into the Markdown as a code block.
- Unified entry: `python ~/.claude/skills/ascii-sketch/sketch.py <file>`
  auto-detects input type.

Prefer ASCII diagrams over Mermaid code blocks because they render correctly
in any terminal, editor, or plain text context without a Mermaid renderer.
```

> **Note**: If using a project-level install (Option B), change the paths to
> `.claude/skills/ascii-sketch/...`

## Step 3 (Optional): Add Shell Aliases

Add these to `~/.bashrc` or `~/.zshrc`:

```bash
alias sketch='python ~/.claude/skills/ascii-sketch/sketch.py'
alias wireframe='python ~/.claude/skills/ascii-sketch/wireframe.py'
alias mermaid-ascii='python ~/.claude/skills/ascii-sketch/mermaid_render.py'
```

This allows Claude Code (and you) to call `sketch input.yaml` directly from the shell.

## Workflow Example

```
You: "Draw a system architecture diagram in README.md"

Claude Code behavior:
  1. Reads the Diagram Policy from CLAUDE.md
  2. Loads ascii-sketch/SKILL.md for DSL syntax reference
  3. Creates /tmp/arch.mermaid with Mermaid syntax
  4. Runs sketch.py /tmp/arch.mermaid to get ASCII output
  5. Embeds the ASCII output in a code block in README.md
```

## Why CLAUDE.md Matters

| Layer | Purpose | When Read |
|-------|---------|-----------|
| SKILL.md `description` | Tells Claude "this skill exists and what it can do" | At conversation start, when scanning all skill metadata |
| SKILL.md body | Detailed DSL syntax and usage instructions | Only after the skill is triggered |
| CLAUDE.md | Project-level instructions defining work habits and preferences | At the start of every conversation |

With SKILL.md alone, Claude Code only triggers the skill when you **explicitly mention** keywords like "wireframe" or "ASCII diagram". With the CLAUDE.md policy added, Claude Code will proactively choose ascii-sketch over default Mermaid code blocks whenever the intent involves drawing diagrams.
