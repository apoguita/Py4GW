"""Pure-Python SVG diff renderer for path snapshot regression failures.

Generates browser-compatible SVG files showing expected vs actual paths overlaid
on a base map of trapezoid geometry. No external dependencies.
"""

from __future__ import annotations

from pathlib import Path

from Py4GWCoreLib.Pathing import NavMesh

DIFF_DIR = Path(__file__).resolve().parent.parent / "diff"


# ---------------------------------------------------------------------------
# SVG primitives
# ---------------------------------------------------------------------------

def _xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _compute_bounds(navmesh: NavMesh) -> tuple[float, float, float, float]:
    """Return (min_x, min_y, max_x, max_y) from all trapezoid geometry."""
    xs: list[float] = []
    ys: list[float] = []
    for t in navmesh.trapezoids.values():
        xs.extend([t.XTL, t.XTR, t.XBL, t.XBR])
        ys.extend([t.YT, t.YB])
    return min(xs), min(ys), max(xs), max(ys)


def _svg_header(min_x: float, min_y: float, max_x: float, max_y: float, title: str) -> str:
    """SVG header with viewBox, Y-flip, and dark background."""
    pad_x = (max_x - min_x) * 0.05 or 100
    pad_y = (max_y - min_y) * 0.05 or 100
    vx = min_x - pad_x
    vw = (max_x - min_x) + 2 * pad_x
    vh = (max_y - min_y) + 2 * pad_y
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{vx} {-max_y - pad_y} {vw} {vh}" '
        f'width="1600" height="{int(1600 * vh / vw)}" '
        f'style="background:#1a1a2e">\n'
        f'<title>{_xml_escape(title)}</title>\n'
        f'<g transform="scale(1,-1)">\n'
    )


def _svg_footer() -> str:
    return '</g>\n</svg>\n'


def _render_trapezoids(navmesh: NavMesh, stroke_width: float) -> str:
    """Render all trapezoids as polygons."""
    lines: list[str] = []
    for t in navmesh.trapezoids.values():
        pts = f"{t.XTL},{t.YT} {t.XTR},{t.YT} {t.XBR},{t.YB} {t.XBL},{t.YB}"
        lines.append(
            f'<polygon points="{pts}" '
            f'fill="#2a2a3e" fill-opacity="0.6" '
            f'stroke="#555" stroke-width="{stroke_width}"/>'
        )
    return '\n'.join(lines)


def _render_legend(min_x: float, max_y: float, pad: float, items: list[tuple[str, str]], stroke_width: float) -> str:
    """Render a legend in the top-left corner (in flipped Y coords)."""
    lines: list[str] = []
    lx = min_x + pad * 0.5
    ly = max_y - pad * 0.3
    spacing = stroke_width * 30
    box_w = stroke_width * 15
    font_size = stroke_width * 20

    for i, (color, label) in enumerate(items):
        y = ly - i * spacing
        if "dash" in color:
            c = color.replace("-dash", "")
            lines.append(
                f'<line x1="{lx}" y1="{y}" x2="{lx + box_w}" y2="{y}" '
                f'stroke="{c}" stroke-width="{stroke_width * 3}" '
                f'stroke-dasharray="{stroke_width * 4},{stroke_width * 2}"/>'
            )
        else:
            lines.append(
                f'<line x1="{lx}" y1="{y}" x2="{lx + box_w}" y2="{y}" '
                f'stroke="{color}" stroke-width="{stroke_width * 3}"/>'
            )
        lines.append(
            f'<g transform="translate({lx + box_w * 1.3},{y}) scale(1,-1)">'
            f'<text font-family="monospace" font-size="{font_size}" '
            f'fill="#ddd" dominant-baseline="middle">{_xml_escape(label)}</text></g>'
        )
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Path diff
# ---------------------------------------------------------------------------

def render_path_diff(name: str, navmesh: NavMesh, expected: list, actual: list) -> None:
    DIFF_DIR.mkdir(parents=True, exist_ok=True)
    min_x, min_y, max_x, max_y = _compute_bounds(navmesh)
    sw = (max_x - min_x) * 0.001
    pad = (max_x - min_x) * 0.05
    marker_r = sw * 3
    endpoint_r = sw * 6

    parts: list[str] = []
    parts.append(_svg_header(min_x, min_y, max_x, max_y, f"Path Diff: {name}"))
    parts.append(_render_trapezoids(navmesh, sw))

    # Expected path (green)
    if expected and len(expected) >= 2:
        pts = ' '.join(f"{p[0]},{p[1]}" for p in expected)
        parts.append(
            f'<polyline points="{pts}" fill="none" '
            f'stroke="#2a2" stroke-width="{sw * 2}" stroke-opacity="0.8"/>'
        )
        for p in expected:
            parts.append(
                f'<circle cx="{p[0]}" cy="{p[1]}" r="{marker_r}" '
                f'fill="#2a2" fill-opacity="0.5"/>'
            )
        # Start/end markers
        parts.append(
            f'<circle cx="{expected[0][0]}" cy="{expected[0][1]}" r="{endpoint_r}" '
            f'fill="none" stroke="#2a2" stroke-width="{sw * 2}"/>'
        )
        parts.append(
            f'<circle cx="{expected[-1][0]}" cy="{expected[-1][1]}" r="{endpoint_r}" '
            f'fill="#2a2" fill-opacity="0.4"/>'
        )

    # Actual path (red)
    if actual and len(actual) >= 2:
        pts = ' '.join(f"{p[0]},{p[1]}" for p in actual)
        parts.append(
            f'<polyline points="{pts}" fill="none" '
            f'stroke="#c22" stroke-width="{sw * 2}" stroke-opacity="0.8"/>'
        )
        for p in actual:
            parts.append(
                f'<circle cx="{p[0]}" cy="{p[1]}" r="{marker_r}" '
                f'fill="#c22" fill-opacity="0.5"/>'
            )
        parts.append(
            f'<circle cx="{actual[0][0]}" cy="{actual[0][1]}" r="{endpoint_r}" '
            f'fill="none" stroke="#c22" stroke-width="{sw * 2}"/>'
        )
        parts.append(
            f'<circle cx="{actual[-1][0]}" cy="{actual[-1][1]}" r="{endpoint_r}" '
            f'fill="#c22" fill-opacity="0.4"/>'
        )

    parts.append(_render_legend(min_x, max_y, pad, [
        ("#2a2", f"Expected ({len(expected)} pts)"),
        ("#c22", f"Actual ({len(actual)} pts)"),
    ], sw))
    parts.append(_svg_footer())

    out = DIFF_DIR / f"{name}.svg"
    out.write_text('\n'.join(parts))
