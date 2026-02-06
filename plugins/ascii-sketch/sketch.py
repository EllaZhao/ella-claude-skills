#!/usr/bin/env python3
"""
ascii-sketch: Unified ASCII rendering tool.

Supports two modes:
  1. UI Wireframes from YAML DSL     (*.yaml / *.yml)
  2. Mermaid diagrams from .mermaid   (*.mermaid / *.mmd, or auto-detect)

Usage:
    python sketch.py dialog.yaml             # wireframe mode
    python sketch.py flow.mermaid            # mermaid mode
    echo "graph LR; A-->B" | python sketch.py - --mermaid
    python sketch.py input.txt --auto        # auto-detect
"""

import sys
import argparse
import os


def detect_mode(text: str, filepath: str = "") -> str:
    """Auto-detect whether input is YAML wireframe or Mermaid."""
    ext = os.path.splitext(filepath)[1].lower() if filepath else ""

    if ext in (".yaml", ".yml"):
        return "wireframe"
    if ext in (".mermaid", ".mmd"):
        return "mermaid"

    # Content-based detection
    stripped = text.strip()
    first_lines = stripped.split("\n")[:5]
    for line in first_lines:
        line = line.strip()
        if line.startswith(("graph ", "flowchart ", "sequenceDiagram")):
            return "mermaid"
        if line.startswith(("title:", "width:", "components:", "panels:", "layout:")):
            return "wireframe"

    # Check for mermaid arrow patterns
    if "-->" in text or "->>" in text:
        return "mermaid"

    return "wireframe"  # default


def main():
    parser = argparse.ArgumentParser(
        description="ASCII Sketch: wireframes + mermaid diagrams"
    )
    parser.add_argument("input", help="Input file, or '-' for stdin")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument("--mermaid", action="store_true", help="Force mermaid mode")
    parser.add_argument("--wireframe", action="store_true", help="Force wireframe mode")
    parser.add_argument("--ascii", action="store_true", help="Use plain ASCII (mermaid only)")
    args = parser.parse_args()

    if args.input == "-":
        text = sys.stdin.read()
        filepath = ""
    else:
        with open(args.input) as f:
            text = f.read()
        filepath = args.input

    # Determine mode
    if args.mermaid:
        mode = "mermaid"
    elif args.wireframe:
        mode = "wireframe"
    else:
        mode = detect_mode(text, filepath)

    # Route to renderer
    if mode == "mermaid":
        from mermaid_render import render_mermaid
        result = render_mermaid(text, use_ascii=args.ascii)
    else:
        from wireframe import parse_yaml, render_layout
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
