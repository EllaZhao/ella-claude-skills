#!/usr/bin/env python3
"""
mermaid_render.py: Pure Python Mermaid → ASCII renderer.

Supports:
  - graph LR / graph TD / graph TB / flowchart LR / flowchart TD
  - Sequence diagrams (sequenceDiagram)

Architecture (mirrors AlexanderGrooff/mermaid-ascii):
  1. Parse: Mermaid text → nodes + edges (or participants + messages)
  2. Layout: Assign grid coordinates via topological layering
  3. Render: Draw boxes + arrows on a 2D character canvas
"""

import re
import sys
from dataclasses import dataclass, field
from collections import defaultdict, deque


# ─── Box Drawing ──────────────────────────────────────────────────────────

BOX_UNI = {
    "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
    "h": "─", "v": "│", "lj": "├", "rj": "┤",
    "tj": "┬", "bj": "┴", "cross": "┼",
    "arrow_r": "►", "arrow_l": "◄", "arrow_d": "▼", "arrow_u": "▲",
    "dash": "┈",
}

BOX_ASCII = {
    "tl": "+", "tr": "+", "bl": "+", "br": "+",
    "h": "-", "v": "|", "lj": "+", "rj": "+",
    "tj": "+", "bj": "+", "cross": "+",
    "arrow_r": ">", "arrow_l": "<", "arrow_d": "v", "arrow_u": "^",
    "dash": ".",
}


# ─── Canvas ───────────────────────────────────────────────────────────────

class Canvas:
    """2D character canvas for drawing."""

    def __init__(self, width: int, height: int):
        self.w = width
        self.h = height
        self.grid = [[" "] * width for _ in range(height)]

    def put(self, x: int, y: int, ch: str):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.grid[y][x] = ch

    def put_str(self, x: int, y: int, s: str):
        for i, ch in enumerate(s):
            self.put(x + i, y, ch)

    def hline(self, x1: int, x2: int, y: int, ch: str = "─"):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.put(x, y, ch)

    def vline(self, x: int, y1: int, y2: int, ch: str = "│"):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.put(x, y, ch)

    def draw_box(self, x: int, y: int, w: int, h: int, b=None):
        """Draw a box at (x, y) with width w and height h."""
        if b is None:
            b = BOX_UNI
        self.put(x, y, b["tl"])
        self.put(x + w - 1, y, b["tr"])
        self.put(x, y + h - 1, b["bl"])
        self.put(x + w - 1, y + h - 1, b["br"])
        self.hline(x + 1, x + w - 2, y, b["h"])
        self.hline(x + 1, x + w - 2, y + h - 1, b["h"])
        self.vline(x, y + 1, y + h - 2, b["v"])
        self.vline(x + w - 1, y + 1, y + h - 2, b["v"])

    def render(self) -> str:
        lines = ["".join(row).rstrip() for row in self.grid]
        while lines and not lines[-1].strip():
            lines.pop()
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
#  FLOWCHART RENDERER
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class FNode:
    id: str
    label: str
    shape: str = "rect"  # rect, round, diamond, stadium
    layer: int = -1
    pos: int = -1        # position within layer
    # Drawing coords (set during layout)
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0


@dataclass
class FEdge:
    src: str
    dst: str
    label: str = ""
    style: str = "solid"  # solid, dotted
    arrow: bool = True


def parse_flowchart(text: str) -> tuple[dict[str, FNode], list[FEdge], str]:
    """Parse mermaid flowchart syntax into nodes and edges.

    Returns (nodes_dict, edges_list, direction).
    """
    nodes: dict[str, FNode] = {}
    edges: list[FEdge] = []
    direction = "LR"  # default

    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line or line.startswith("%%"):
            continue

        # Direction line
        m = re.match(r"^(graph|flowchart)\s+(LR|RL|TD|TB|BT)\s*$", line, re.I)
        if m:
            direction = m.group(2).upper()
            continue

        # Skip style/class definitions
        if re.match(r"^(classDef|class|style|linkStyle|subgraph|end)\b", line, re.I):
            continue

        # Parse edges: A --> B, A -->|label| B, A --- B, A -.-> B
        # Also handle: A --> B & C (fan-out), A & B --> C
        # Also handle node definitions inline: A[Label] --> B[Label]

        _parse_edge_line(line, nodes, edges)

    return nodes, edges, direction


def _ensure_node(nodes: dict, nid: str, label: str = "", shape: str = "rect"):
    """Create node if not exists, update label if provided."""
    nid = nid.strip()
    if not nid:
        return
    if nid not in nodes:
        nodes[nid] = FNode(id=nid, label=label or nid, shape=shape)
    elif label:
        nodes[nid].label = label
        nodes[nid].shape = shape


def _parse_node_ref(raw: str, nodes: dict) -> str:
    """Parse a node reference like 'A', 'A[Label]', 'A(Label)', 'A{Label}', 'A([Label])'
    Returns the node id.
    """
    raw = raw.strip()
    if not raw:
        return ""

    # A([Stadium Label])
    m = re.match(r"^(\w+)\(\[(.+?)\]\)$", raw)
    if m:
        _ensure_node(nodes, m.group(1), m.group(2), "stadium")
        return m.group(1)

    # A{Label} - diamond
    m = re.match(r"^(\w+)\{(.+?)\}$", raw)
    if m:
        _ensure_node(nodes, m.group(1), m.group(2), "diamond")
        return m.group(1)

    # A(Label) - rounded
    m = re.match(r"^(\w+)\((.+?)\)$", raw)
    if m:
        _ensure_node(nodes, m.group(1), m.group(2), "round")
        return m.group(1)

    # A[Label] - rect
    m = re.match(r"^(\w+)\[(.+?)\]$", raw)
    if m:
        _ensure_node(nodes, m.group(1), m.group(2), "rect")
        return m.group(1)

    # A[[Label]] - subroutine
    m = re.match(r"^(\w+)\[\[(.+?)\]\]$", raw)
    if m:
        _ensure_node(nodes, m.group(1), m.group(2), "rect")
        return m.group(1)

    # Plain ID
    m = re.match(r"^(\w+)$", raw)
    if m:
        _ensure_node(nodes, m.group(1))
        return m.group(1)

    return raw


def _parse_edge_line(line: str, nodes: dict, edges: list):
    """Parse a line that may contain one or more chained edges.

    Handles patterns like:
      A --> B
      A -->|label| B
      A --> B --> C  (chained)
      A --> B & C    (fan-out)
      A & B --> C    (fan-in)
      A -.-> B       (dotted)
      A ==> B        (thick)
    """
    # Master regex: match arrow operators including labels
    # This splits "A -->|Yes| B --> C" into ["A ", "-->|Yes|", " B ", "-->", " C"]
    arrow_re = re.compile(
        r'(\s*'
        r'(?:--+>|==+>|-\.+-?>)'       # basic arrows: -->, ===>, -.->
        r'(?:\|[^|]*\|)?'              # optional |label| AFTER arrow
        r'|'
        r'(?:--+|==+|-\.+-?)'          # lines without arrowhead
        r'(?:\|[^|]*\|)?'              # optional |label|
        r'(?:>)?'                       # optional arrowhead
        r'\s*)'
    )

    # Alternative simpler approach: use a dedicated regex
    # Pattern: captures  -->  or  -->|label|  or  -.->  or  ==>  etc.
    split_re = re.compile(
        r'(--+>?\|[^|]*\|>?|--+>|==+>|-\.+-?>|==+|--+)'
    )

    parts = split_re.split(line)
    # parts: [node_ref, arrow, node_ref, arrow, node_ref, ...]

    if len(parts) < 3:
        _parse_node_ref(line, nodes)
        return

    i = 0
    while i < len(parts) - 2:
        src_part = parts[i].strip()
        arrow_part = parts[i + 1].strip()
        dst_part = parts[i + 2].strip()

        # Handle & (fan-out/fan-in)
        src_ids = [s.strip() for s in src_part.split("&") if s.strip()]
        dst_ids = [d.strip() for d in dst_part.split("&") if d.strip()]

        # Determine arrow style and properties
        style = "solid"
        has_arrow = ">" in arrow_part
        label = ""

        if "-." in arrow_part:
            style = "dotted"
        elif "==" in arrow_part:
            style = "solid"

        # Extract label from --|label| or -->|label|
        lm = re.search(r'\|([^|]+)\|', arrow_part)
        if lm:
            label = lm.group(1)

        for s in src_ids:
            sid = _parse_node_ref(s, nodes)
            if not sid:
                continue
            for d in dst_ids:
                did = _parse_node_ref(d, nodes)
                if not did:
                    continue
                edges.append(FEdge(src=sid, dst=did, label=label, style=style, arrow=has_arrow))

        i += 2


def layout_flowchart(
    nodes: dict[str, FNode],
    edges: list[FEdge],
    direction: str,
    box_pad: int = 1,
    spacing_x: int = 6,
    spacing_y: int = 2,
) -> tuple[int, int]:
    """Assign x,y coordinates to nodes. Returns (canvas_width, canvas_height).

    Uses topological layering (like mermaid-ascii's grid system).
    """
    # Build adjacency
    adj: dict[str, list[str]] = defaultdict(list)
    in_deg: dict[str, int] = defaultdict(int)
    for nid in nodes:
        in_deg.setdefault(nid, 0)
    for e in edges:
        adj[e.src].append(e.dst)
        in_deg[e.dst] = in_deg.get(e.dst, 0) + 1

    # Topological sort → assign layers (BFS Kahn's)
    queue = deque([n for n in nodes if in_deg[n] == 0])
    if not queue:
        queue = deque([next(iter(nodes))])  # fallback: pick first

    layers: dict[int, list[str]] = defaultdict(list)
    visited = set()
    while queue:
        nid = queue.popleft()
        if nid in visited:
            continue
        visited.add(nid)
        node = nodes[nid]
        # Layer = max layer of predecessors + 1
        pred_layers = []
        for e in edges:
            if e.dst == nid and e.src in visited:
                pred_layers.append(nodes[e.src].layer)
        node.layer = (max(pred_layers) + 1) if pred_layers else 0
        layers[node.layer].append(nid)
        for neighbor in adj[nid]:
            in_deg[neighbor] -= 1
            if in_deg[neighbor] <= 0:
                queue.append(neighbor)

    # Catch any unvisited nodes
    for nid in nodes:
        if nid not in visited:
            nodes[nid].layer = 0
            layers[0].append(nid)

    # Calculate box sizes
    for node in nodes.values():
        text_w = len(node.label)
        node.w = text_w + 2 + box_pad * 2  # borders + padding
        node.h = 3 + box_pad * 2           # top border + padding + text + padding + bottom border

    is_horizontal = direction in ("LR", "RL")

    if is_horizontal:
        # Layers go left→right, nodes in a layer go top→bottom
        max_layers = max(layers.keys()) + 1 if layers else 1
        # For each layer, compute x as cumulative max-width + spacing
        layer_x = {}
        cx = 0
        layer_order = range(max_layers)
        if direction == "RL":
            layer_order = reversed(range(max_layers))

        for li in layer_order:
            layer_nodes = layers.get(li, [])
            max_w = max((nodes[n].w for n in layer_nodes), default=5)
            layer_x[li] = cx
            # Center narrower boxes in the layer
            for idx, nid in enumerate(layer_nodes):
                node = nodes[nid]
                node.pos = idx
                node.x = cx + (max_w - node.w) // 2
            cx += max_w + spacing_x

        # Assign y positions within each layer
        for li, layer_nodes in layers.items():
            cy = 0
            for nid in layer_nodes:
                node = nodes[nid]
                node.y = cy
                cy += node.h + spacing_y

        canvas_w = cx - spacing_x + 2
        max_y = max((n.y + n.h for n in nodes.values()), default=5)
        canvas_h = max_y + 1

    else:
        # TD/TB: layers go top→bottom, nodes go left→right
        max_layers = max(layers.keys()) + 1 if layers else 1
        layer_y = {}
        cy = 0
        for li in range(max_layers):
            layer_nodes = layers.get(li, [])
            max_h = max((nodes[n].h for n in layer_nodes), default=3)
            layer_y[li] = cy
            for idx, nid in enumerate(layer_nodes):
                node = nodes[nid]
                node.pos = idx
                node.y = cy
            cy += max_h + spacing_y + 1  # extra for vertical arrows

        # Assign x within each layer
        for li, layer_nodes in layers.items():
            cx = 0
            for nid in layer_nodes:
                node = nodes[nid]
                node.x = cx
                cx += node.w + spacing_x

        max_x = max((n.x + n.w for n in nodes.values()), default=10)
        canvas_w = max_x + 2
        canvas_h = cy

    return canvas_w, canvas_h


def render_flowchart(
    nodes: dict[str, FNode],
    edges: list[FEdge],
    direction: str,
    use_ascii: bool = False,
) -> str:
    """Render flowchart to string."""
    b = BOX_ASCII if use_ascii else BOX_UNI

    canvas_w, canvas_h = layout_flowchart(nodes, edges, direction)
    canvas = Canvas(canvas_w, canvas_h)

    # Draw nodes
    for node in nodes.values():
        canvas.draw_box(node.x, node.y, node.w, node.h, b)
        # Center text in box (both horizontally and vertically)
        tx = node.x + 1 + (node.w - 2 - len(node.label)) // 2
        ty = node.y + node.h // 2
        canvas.put_str(tx, ty, node.label)

    is_horizontal = direction in ("LR", "RL")

    # Draw edges - render L-shaped first, then straight edges on top
    # This prevents L-shaped edge segments from overwriting ├ connectors
    def edge_sort_key(e):
        s, d = nodes.get(e.src), nodes.get(e.dst)
        if not s or not d:
            return 0
        if is_horizontal:
            return 0 if (s.y + s.h // 2) != (d.y + d.h // 2) else 1
        else:
            return 0 if (s.x + s.w // 2) != (d.x + d.w // 2) else 1

    sorted_edges = sorted(edges, key=edge_sort_key)

    for edge in sorted_edges:
        src = nodes.get(edge.src)
        dst = nodes.get(edge.dst)
        if not src or not dst:
            continue

        line_ch = b["dash"] if edge.style == "dotted" else b["h"]
        vline_ch = b["dash"] if edge.style == "dotted" else b["v"]

        if is_horizontal:
            _draw_edge_horizontal(canvas, src, dst, edge, b, line_ch, vline_ch, direction)
        else:
            _draw_edge_vertical(canvas, src, dst, edge, b, line_ch, vline_ch)

    return canvas.render()


def _draw_edge_horizontal(canvas, src, dst, edge, b, line_ch, vline_ch, direction):
    """Draw an edge for LR/RL layouts.

    Strategy (like mermaid-ascii):
    - Same row: straight horizontal  src_right ──► dst_left
    - Different row: exit src bottom, go horizontal, enter dst left
    """
    arrow_ch = b["arrow_l"] if direction == "RL" else b["arrow_r"]

    src_mid_y = src.y + src.h // 2
    dst_mid_y = dst.y + dst.h // 2

    if src_mid_y == dst_mid_y:
        # Straight horizontal
        sx = src.x + src.w - 1 if direction != "RL" else src.x
        dx = dst.x if direction != "RL" else dst.x + dst.w - 1
        # Use ├ at source exit point
        canvas.put(sx, src_mid_y, b["lj"] if direction != "RL" else b["rj"])
        # Draw line between boxes (not on borders)
        for x in range(sx + 1, dx):
            canvas.put(x, src_mid_y, line_ch)
        # Arrow just before destination border
        if edge.arrow and abs(dx - sx) > 1:
            arrow_pos = dx - 1 if direction != "RL" else dx + 1
            canvas.put(arrow_pos, dst_mid_y, arrow_ch)
        if edge.label:
            mid_x = (sx + dx) // 2 - len(edge.label) // 2
            canvas.put_str(max(0, mid_x), src_mid_y - 1, edge.label)
    else:
        # L-shaped: exit from bottom/top of src, horizontal, then to dst
        # Exit point: bottom center of src
        exit_x = src.x + src.w // 2
        exit_y = src.y + src.h - 1  # bottom of src

        # Enter point: left middle of dst
        enter_x = dst.x if direction != "RL" else dst.x + dst.w - 1
        enter_y = dst.y + dst.h // 2

        # Draw vertical down from src bottom
        for y in range(exit_y + 1, enter_y + 1):
            canvas.put(exit_x, y, vline_ch)

        # Draw horizontal to dst (stop before border)
        for x in range(min(exit_x, enter_x) + 1, max(exit_x, enter_x)):
            canvas.put(x, enter_y, line_ch)

        # Arrow just before destination border
        if edge.arrow and abs(enter_x - exit_x) > 1:
            arrow_pos = enter_x - 1 if enter_x > exit_x else enter_x + 1
            canvas.put(arrow_pos, enter_y, arrow_ch)

        if edge.label:
            label_x = min(exit_x, enter_x) + 1
            canvas.put_str(label_x, enter_y - 1, edge.label)


def _draw_edge_vertical(canvas, src, dst, edge, b, line_ch, vline_ch):
    """Draw an edge for TD/TB layouts."""
    sx = src.x + src.w // 2
    sy = src.y + src.h - 1
    dx = dst.x + dst.w // 2
    dy = dst.y
    arrow_ch = b["arrow_d"]

    if sx == dx:
        # Straight vertical line
        for y in range(sy + 1, dy):
            canvas.put(sx, y, vline_ch)
        if edge.arrow:
            canvas.put(dx, max(sy + 1, dy - 1), arrow_ch)
    else:
        # L-shaped: exit src down → go horizontal → enter dst down
        mid_y = sy + (dy - sy) // 2
        # Vertical from src bottom to mid
        for y in range(sy + 1, mid_y):
            canvas.put(sx, y, vline_ch)
        # Horizontal at mid_y
        x_start, x_end = min(sx, dx), max(sx, dx)
        for x in range(x_start, x_end + 1):
            canvas.put(x, mid_y, line_ch)
        # Vertical from mid to dst top
        for y in range(mid_y + 1, dy):
            canvas.put(dx, y, vline_ch)
        if edge.arrow:
            canvas.put(dx, max(mid_y + 1, dy - 1), arrow_ch)

    if edge.label:
        lx = max(sx, dx) + 2
        ly = (sy + dy) // 2
        canvas.put_str(lx, ly, edge.label)


# ═══════════════════════════════════════════════════════════════════════════
#  SEQUENCE DIAGRAM RENDERER
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Participant:
    name: str
    x: int = 0  # center x
    col_w: int = 0  # header box width


@dataclass
class Message:
    src: str
    dst: str
    text: str
    style: str = "solid"  # solid (->>) or dashed (-->>)
    msg_type: str = "arrow"  # arrow, note


def parse_sequence(text: str) -> tuple[list[Participant], list[Message]]:
    """Parse sequenceDiagram syntax."""
    participants: dict[str, Participant] = {}
    messages: list[Message] = []
    part_order: list[str] = []

    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line or line == "sequenceDiagram" or line.startswith("%%"):
            continue

        # Participant declaration
        m = re.match(r"^participant\s+(\S+)(?:\s+as\s+(.+))?$", line, re.I)
        if m:
            pid = m.group(1)
            label = m.group(2) or pid
            if pid not in participants:
                participants[pid] = Participant(name=label)
                part_order.append(pid)
            continue

        # Message: Alice->>Bob: Hello  or  Alice-->>Bob: Hi
        m = re.match(r"^(\S+?)\s*(--?>>?|--?>|\.\.>|->>|->)\s*(\S+?)\s*:\s*(.*)$", line)
        if m:
            src, arrow, dst, msg_text = m.groups()
            style = "dotted" if "--" in arrow else "solid"
            # Auto-create participants
            for p in (src, dst):
                if p not in participants:
                    participants[p] = Participant(name=p)
                    part_order.append(p)
            messages.append(Message(src=src, dst=dst, text=msg_text.strip(), style=style))
            continue

    # Build ordered list
    ordered = [participants[pid] for pid in part_order]
    return ordered, messages


def render_sequence(
    participants: list[Participant],
    messages: list[Message],
    use_ascii: bool = False,
) -> str:
    """Render a sequence diagram."""
    b = BOX_ASCII if use_ascii else BOX_UNI

    if not participants:
        return ""

    # Calculate column widths
    spacing = 4
    min_col_w = 12

    # Consider message text length for spacing
    pid_map = {}
    for i, p in enumerate(participants):
        pid_map[p.name] = i
        p.col_w = max(len(p.name) + 4, min_col_w)  # box width

    # Adjust spacing based on message widths
    col_spacing = [spacing] * len(participants)
    for msg in messages:
        si = pid_map.get(msg.src, 0)
        di = pid_map.get(msg.dst, 0)
        if si == di:
            continue
        msg_w = len(msg.text) + 4  # arrow + padding
        cols_between = abs(di - si)
        min_span = msg_w
        curr_span = sum(
            participants[j].col_w // 2 + col_spacing[j] + participants[j + 1].col_w // 2
            for j in range(min(si, di), max(si, di))
        ) if cols_between > 0 else 0
        if curr_span < min_span and cols_between > 0:
            extra = (min_span - curr_span) // cols_between + 1
            for j in range(min(si, di), max(si, di)):
                col_spacing[j] = max(col_spacing[j], spacing + extra)

    # Calculate x positions (center of each participant)
    cx = 0
    for i, p in enumerate(participants):
        if i == 0:
            p.x = p.col_w // 2
            cx = p.col_w
        else:
            cx += col_spacing[i - 1]
            p.x = cx + p.col_w // 2
            cx += p.col_w

    total_w = cx + 2
    # Header height + messages + footer
    header_h = 3
    msg_start_y = header_h + 1
    msg_spacing = 3
    total_h = msg_start_y + len(messages) * msg_spacing + 2

    canvas = Canvas(total_w, total_h)

    # Draw participant headers
    for p in participants:
        bx = p.x - p.col_w // 2
        canvas.draw_box(bx, 0, p.col_w, 3, b)
        tx = p.x - len(p.name) // 2
        canvas.put_str(tx, 1, p.name)

    # Draw lifelines
    for p in participants:
        for y in range(header_h, total_h - 1):
            canvas.put(p.x, y, b["v"])

    # Draw messages
    for mi, msg in enumerate(messages):
        y = msg_start_y + mi * msg_spacing + 1
        si = pid_map.get(msg.src, 0)
        di = pid_map.get(msg.dst, 0)
        src_p = participants[si]
        dst_p = participants[di]

        sx = src_p.x
        dx = dst_p.x

        if sx == dx:
            continue  # self-message (skip for simplicity)

        line_ch = b["dash"] if msg.style == "dotted" else b["h"]

        if dx > sx:
            # Left to right
            for x in range(sx + 1, dx):
                canvas.put(x, y, line_ch)
            canvas.put(dx, y, b["arrow_r"])
        else:
            # Right to left
            for x in range(dx + 1, sx):
                canvas.put(x, y, line_ch)
            canvas.put(dx, y, b["arrow_l"])

        # Message label above the arrow
        label_x = min(sx, dx) + (abs(dx - sx) - len(msg.text)) // 2
        canvas.put_str(max(0, label_x), y - 1, msg.text)

    return canvas.render()


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def detect_diagram_type(text: str) -> str:
    """Detect if text is a flowchart or sequence diagram."""
    stripped = text.strip()
    for line in stripped.split("\n"):
        line = line.strip()
        if line.lower().startswith("sequencediagram"):
            return "sequence"
        if re.match(r"^(graph|flowchart)\s+(LR|RL|TD|TB|BT)", line, re.I):
            return "flowchart"
    return "flowchart"  # default


def render_mermaid(text: str, use_ascii: bool = False) -> str:
    """Render a mermaid diagram to ASCII string."""
    dtype = detect_diagram_type(text)

    if dtype == "sequence":
        participants, messages = parse_sequence(text)
        return render_sequence(participants, messages, use_ascii)
    else:
        nodes, edges, direction = parse_flowchart(text)
        return render_flowchart(nodes, edges, direction, use_ascii)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Render Mermaid diagrams as ASCII art")
    parser.add_argument("input", help="Mermaid file path, or '-' for stdin")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument("--ascii", action="store_true", help="Use plain ASCII instead of Unicode")
    args = parser.parse_args()

    if args.input == "-":
        text = sys.stdin.read()
    else:
        with open(args.input) as f:
            text = f.read()

    result = render_mermaid(text, use_ascii=args.ascii)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result + "\n")
        print(f"Written to {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
