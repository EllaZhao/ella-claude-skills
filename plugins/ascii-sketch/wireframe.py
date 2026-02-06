#!/usr/bin/env python3
"""
ascii-wireframe: Render UI wireframes as ASCII art from a simple YAML DSL.

Inspired by mermaid-ascii's architecture: DSL → model → grid → render.
Designed for use in Claude Code as a skill script.

Usage:
    python wireframe.py input.yaml          # render to stdout
    python wireframe.py input.yaml -o out.txt  # render to file
    echo "YAML" | python wireframe.py -      # pipe mode
"""

import sys
import yaml
import argparse
import textwrap
from dataclasses import dataclass, field
from typing import Optional

# ─── Box Drawing Characters ───────────────────────────────────────────────
# Borrowing mermaid-ascii's approach: Unicode box-drawing for clean output
BOX = {
    "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
    "h": "─", "v": "│", "tj": "┬", "bj": "┴",
    "lj": "├", "rj": "┤", "cross": "┼",
}

# ─── Data Model ───────────────────────────────────────────────────────────

@dataclass
class Component:
    """A UI component in the wireframe."""
    type: str           # text, button, radio, checkbox, input, select, divider, separator, spacer, progress, tabs, table
    text: str = ""
    checked: bool = False
    selected: bool = False
    align: str = "left"   # left, center, right
    width: Optional[int] = None
    options: list = field(default_factory=list)
    columns: list = field(default_factory=list)
    rows: list = field(default_factory=list)
    items: list = field(default_factory=list)  # for tabs


@dataclass
class Panel:
    """A panel/container with a title and components."""
    title: str = ""
    width: int = 40
    components: list = field(default_factory=list)
    padding: int = 1


def parse_component(raw) -> Component:
    """Parse a single component from YAML dict or string."""
    if isinstance(raw, str):
        return Component(type="text", text=raw)
    if not isinstance(raw, dict):
        return Component(type="text", text=str(raw))

    ctype = raw.get("type", "text")

    if ctype == "table":
        return Component(
            type="table",
            columns=raw.get("columns", []),
            rows=raw.get("rows", []),
        )

    if ctype == "tabs":
        return Component(
            type="tabs",
            items=raw.get("items", []),
            selected=raw.get("active", 0),
        )

    return Component(
        type=ctype,
        text=raw.get("text", raw.get("label", "")),
        checked=raw.get("checked", False),
        selected=raw.get("selected", False),
        align=raw.get("align", "left"),
        width=raw.get("width"),
        options=raw.get("options", []),
    )


def parse_panel(raw: dict) -> Panel:
    """Parse a panel definition from YAML."""
    panel = Panel(
        title=raw.get("title", ""),
        width=raw.get("width", 40),
        padding=raw.get("padding", 1),
    )
    for comp_raw in raw.get("components", []):
        panel.components.append(parse_component(comp_raw))
    return panel


# ─── Renderers (one per component type) ──────────────────────────────────

def _pad(text: str, width: int, align: str = "left") -> str:
    """Pad text to width with alignment."""
    if align == "center":
        return text.center(width)
    elif align == "right":
        return text.rjust(width)
    return text.ljust(width)


def render_text(comp: Component, inner_w: int) -> list[str]:
    """Render plain text, supporting multi-line wrapping."""
    if not comp.text:
        return [" " * inner_w]
    lines = []
    for raw_line in comp.text.split("\n"):
        wrapped = textwrap.wrap(raw_line, inner_w) if raw_line.strip() else [""]
        for w in wrapped:
            lines.append(_pad(w, inner_w, comp.align))
    return lines


def render_button(comp: Component, inner_w: int) -> list[str]:
    """Render a button like [OK] or [Cancel]."""
    btn = f"[{comp.text}]"
    return [_pad(btn, inner_w, comp.align)]


def render_button_row(comp: Component, inner_w: int) -> list[str]:
    """Render multiple buttons in a row, e.g., options: [Cancel, OK]."""
    buttons = comp.options if comp.options else [comp.text]
    btn_strs = [f"[{b}]" for b in buttons]
    row = "  ".join(btn_strs)
    return [_pad(row, inner_w, comp.align)]


def render_radio(comp: Component, inner_w: int) -> list[str]:
    """Render a radio button like (*) Selected or ( ) Unselected."""
    marker = "(*)" if comp.selected else "( )"
    text = f"{marker} {comp.text}"
    return [_pad(text, inner_w, comp.align)]


def render_checkbox(comp: Component, inner_w: int) -> list[str]:
    """Render a checkbox like [X] Checked or [ ] Unchecked."""
    marker = "[X]" if comp.checked else "[ ]"
    text = f"{marker} {comp.text}"
    return [_pad(text, inner_w, comp.align)]


def render_input(comp: Component, inner_w: int) -> list[str]:
    """Render a text input field.

    align="inline" puts label and field on the same line: Label [value___]
    """
    if comp.align == "inline" and comp.text:
        label = f"{comp.text} "
        field_w = comp.width or (inner_w - len(label) - 2)
        placeholder = comp.options[0] if comp.options else ""
        content = placeholder[:field_w].ljust(field_w, "_")
        row = f"{label}[{content}]"
        return [_pad(row, inner_w)]
    lines = []
    if comp.text:
        lines.append(_pad(comp.text, inner_w))
    field_w = comp.width or (inner_w - 2)
    placeholder = comp.options[0] if comp.options else ""
    content = placeholder[:field_w].ljust(field_w, "_")
    field_str = f"[{content}]"
    lines.append(_pad(field_str, inner_w))
    return lines


def render_select(comp: Component, inner_w: int) -> list[str]:
    """Render a dropdown select.

    align="inline" puts label and dropdown on the same line: Label [value  v]
    """
    if comp.align == "inline" and comp.text:
        label = f"{comp.text} "
        current = comp.options[0] if comp.options else ""
        sel_w = comp.width or (inner_w - len(label) - 4)
        row = f"{label}[{current:<{sel_w}} ▼]"
        return [_pad(row, inner_w)]
    lines = []
    if comp.text:
        lines.append(_pad(comp.text, inner_w))
    current = comp.options[0] if comp.options else ""
    sel_w = comp.width or (inner_w - 4)
    field_str = f"[{current:<{sel_w}} ▼]"
    lines.append(_pad(field_str, inner_w))
    return lines


def render_divider(comp: Component, inner_w: int) -> list[str]:
    """Render a horizontal divider (connects to panel borders)."""
    # Returns a special marker that the panel renderer will handle
    return [f"__DIVIDER__"]


def render_separator(comp: Component, inner_w: int) -> list[str]:
    """Render a lighter separator (doesn't connect to borders)."""
    line = BOX["h"] * inner_w
    return [line]


def render_spacer(comp: Component, inner_w: int) -> list[str]:
    """Render empty space."""
    return [" " * inner_w]


def render_progress(comp: Component, inner_w: int) -> list[str]:
    """Render a progress bar."""
    lines = []
    if comp.text:
        lines.append(_pad(comp.text, inner_w))
    bar_w = inner_w - 2
    filled = int(bar_w * (comp.width or 50) / 100)
    bar = "█" * filled + "░" * (bar_w - filled)
    lines.append(f"[{bar}]".ljust(inner_w))
    return lines


def render_tabs(comp: Component, inner_w: int) -> list[str]:
    """Render tab headers."""
    parts = []
    for i, item in enumerate(comp.items):
        if i == comp.selected:
            parts.append(f"[{item}]")
        else:
            parts.append(f" {item} ")
    row = " ".join(parts)
    lines = [_pad(row, inner_w, comp.align)]
    lines.append(BOX["h"] * inner_w)
    return lines


def render_table(comp: Component, inner_w: int) -> list[str]:
    """Render a simple table."""
    cols = comp.columns
    rows = comp.rows
    if not cols:
        return [" " * inner_w]

    # Calculate column widths
    n = len(cols)
    col_widths = [len(str(c)) for c in cols]
    for row in rows:
        for i, cell in enumerate(row):
            if i < n:
                col_widths[i] = max(col_widths[i], len(str(cell)))

    # Fit to inner_w: separators take (n-1) * 3 chars for " │ "
    total = sum(col_widths) + (n - 1) * 3
    if total > inner_w:
        # Shrink proportionally
        avail = inner_w - (n - 1) * 3
        ratio = avail / sum(col_widths)
        col_widths = [max(3, int(w * ratio)) for w in col_widths]

    def format_row(cells):
        parts = []
        for i, cell in enumerate(cells):
            w = col_widths[i] if i < len(col_widths) else 8
            parts.append(str(cell)[:w].ljust(w))
        return " │ ".join(parts)

    lines = []
    header = format_row(cols)
    lines.append(_pad(header, inner_w))
    sep = "─┼─".join(BOX["h"] * w for w in col_widths)
    lines.append(_pad(sep, inner_w))
    for row in rows:
        lines.append(_pad(format_row(row), inner_w))
    return lines


RENDERERS = {
    "text": render_text,
    "button": render_button,
    "button_row": render_button_row,
    "buttons": render_button_row,
    "radio": render_radio,
    "checkbox": render_checkbox,
    "input": render_input,
    "select": render_select,
    "divider": render_divider,
    "separator": render_separator,
    "spacer": render_spacer,
    "progress": render_progress,
    "tabs": render_tabs,
    "table": render_table,
}


# ─── Panel Renderer ──────────────────────────────────────────────────────

def render_panel(panel: Panel) -> str:
    """Render a complete panel with border and all components.

    Architecture (borrowed from mermaid-ascii):
    1. Parse components → internal model
    2. Render each component to lines (grid cells)
    3. Compose into bordered panel (final drawing)
    """
    pad = panel.padding
    inner_w = panel.width - 2 - pad * 2  # subtract borders and padding
    if inner_w < 4:
        inner_w = 4
        panel.width = inner_w + 2 + pad * 2

    output_lines = []

    # Top border
    top = BOX["tl"] + BOX["h"] * (panel.width - 2) + BOX["tr"]
    output_lines.append(top)

    # Title
    if panel.title:
        title_text = " " * pad + _pad(panel.title, inner_w) + " " * pad
        output_lines.append(BOX["v"] + title_text + BOX["v"])
        # Title divider
        output_lines.append(BOX["lj"] + BOX["h"] * (panel.width - 2) + BOX["rj"])

    # Components
    for comp in panel.components:
        renderer = RENDERERS.get(comp.type, render_text)
        lines = renderer(comp, inner_w)

        for line in lines:
            if line == "__DIVIDER__":
                output_lines.append(
                    BOX["lj"] + BOX["h"] * (panel.width - 2) + BOX["rj"]
                )
            else:
                padded = " " * pad + line + " " * pad
                # Ensure exact width
                content = padded[:panel.width - 2].ljust(panel.width - 2)
                output_lines.append(BOX["v"] + content + BOX["v"])

    # Bottom border
    bottom = BOX["bl"] + BOX["h"] * (panel.width - 2) + BOX["br"]
    output_lines.append(bottom)

    return "\n".join(output_lines)


# ─── Multi-panel Layout ──────────────────────────────────────────────────

def render_layout(panels: list[Panel], layout: str = "vertical") -> str:
    """Render multiple panels, vertical (stacked) or horizontal (side by side)."""
    if layout == "horizontal":
        rendered = [render_panel(p).split("\n") for p in panels]
        # Pad to same height
        max_h = max(len(r) for r in rendered)
        for r in rendered:
            w = len(r[0]) if r else 0
            while len(r) < max_h:
                r.append(" " * w)
        # Join side by side
        lines = []
        for row_parts in zip(*rendered):
            lines.append("  ".join(row_parts))
        return "\n".join(lines)
    else:
        return "\n".join(render_panel(p) for p in panels)


# ─── YAML Parser ─────────────────────────────────────────────────────────

def parse_yaml(text: str) -> tuple[list[Panel], str]:
    """Parse YAML DSL into panels and layout direction."""
    data = yaml.safe_load(text)
    if not data:
        raise ValueError("Empty YAML input")

    layout = data.get("layout", "vertical")

    panels_raw = data.get("panels", [])
    if not panels_raw:
        # Single panel mode: treat entire doc as one panel
        panels_raw = [data]

    panels = [parse_panel(p) for p in panels_raw]
    return panels, layout


# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Render ASCII UI wireframes from YAML DSL"
    )
    parser.add_argument("input", help="YAML file path, or '-' for stdin")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    if args.input == "-":
        text = sys.stdin.read()
    else:
        with open(args.input) as f:
            text = f.read()

    panels, layout = parse_yaml(text)
    result = render_layout(panels, layout)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result + "\n")
        print(f"Written to {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
