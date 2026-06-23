from __future__ import annotations

import os
from pathlib import Path

from fetch_contributions import calendar_from_environment
from svg_common import CELL_SIZE, LEFT, TOP, all_days, cell_xy, geometry, labels, rounded_cell, svg_open, write_svg

DURATION_SECONDS = 5


def target_brackets(x: int, y: int, week_index: int, week_count: int) -> str:
    margin, arm = 2, 4
    x0, y0 = x - margin, y - margin
    x1, y1 = x + CELL_SIZE + margin, y + CELL_SIZE + margin
    delay = (week_index / max(1, week_count - 1)) * DURATION_SECONDS
    path = (
        f"M{x0 + arm},{y0} H{x0} V{y0 + arm} "
        f"M{x1 - arm},{y0} H{x1} V{y0 + arm} "
        f"M{x0},{y1 - arm} V{y1} H{x0 + arm} "
        f"M{x1},{y1 - arm} V{y1} H{x1 - arm}"
    )
    return (
        f'    <path d="{path}" fill="none" stroke="#ff4968" stroke-width="1.2" '
        f'opacity="0" filter="url(#targetGlow)"><animate attributeName="opacity" '
        f'values="0;1;0" dur="0.85s" begin="{delay:.3f}s" repeatCount="indefinite"/></path>\n'
    )


def build_svg() -> str:
    calendar = calendar_from_environment()
    geo = geometry(calendar)
    week_count = len(calendar.weeks)
    scan_start = LEFT - 8
    scan_end = LEFT + geo.graph_width + 8

    parts = [svg_open(calendar, "CCG investigation scanner")]
    parts.append(f'''  <defs>
    <linearGradient id="scannerTrail" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#ff1744" stop-opacity="0"/>
      <stop offset="0.75" stop-color="#ff1744" stop-opacity="0.06"/>
      <stop offset="1" stop-color="#ff1744" stop-opacity="0.38"/>
    </linearGradient>
    <filter id="scannerGlow" x="-100%" y="-30%" width="300%" height="160%">
      <feGaussianBlur stdDeviation="3.5" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="targetGlow" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="1.7" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="100%" height="100%" rx="12" fill="#050505"/>
  <rect x="1" y="1" width="{geo.width - 2}" height="{geo.height - 2}" rx="12" fill="none" stroke="#292929"/>
''')
    parts.append(labels(calendar, "CCG SCAN ACTIVE"))
    parts.append('  <g id="contribution-grid">\n')
    for day in all_days(calendar):
        parts.append('    ' + rounded_cell(day) + '\n')
    parts.append('  </g>\n  <g id="targets">\n')
    for day in all_days(calendar):
        if day.count > 0:
            x, y = cell_xy(day)
            parts.append(target_brackets(x, y, day.week_index, week_count))
    parts.append('  </g>\n')

    parts.append(f'''  <g>
    <rect x="{scan_start - 85}" y="{TOP - 8}" width="85" height="{geo.graph_height + 16}" fill="url(#scannerTrail)">
      <animate attributeName="x" from="{scan_start - 85}" to="{scan_end - 85}" dur="{DURATION_SECONDS}s" repeatCount="indefinite"/>
    </rect>
    <line x1="{scan_start}" x2="{scan_start}" y1="{TOP - 10}" y2="{TOP + geo.graph_height + 10}" stroke="#ff1744" stroke-width="2" filter="url(#scannerGlow)">
      <animate attributeName="x1" from="{scan_start}" to="{scan_end}" dur="{DURATION_SECONDS}s" repeatCount="indefinite"/>
      <animate attributeName="x2" from="{scan_start}" to="{scan_end}" dur="{DURATION_SECONDS}s" repeatCount="indefinite"/>
    </line>
    <circle cx="{scan_start}" cy="{TOP - 15}" r="3" fill="#ff1744" filter="url(#scannerGlow)">
      <animate attributeName="cx" from="{scan_start}" to="{scan_end}" dur="{DURATION_SECONDS}s" repeatCount="indefinite"/>
    </circle>
  </g>
  <text x="{geo.width - 24}" y="{geo.height - 18}" text-anchor="end" fill="#555555" font-family="monospace" font-size="9">TARGETING ACTIVE CELLS // YEARLY CONTRIBUTION ARRAY</text>
</svg>
''')
    return "".join(parts)


if __name__ == "__main__":
    output_path = os.environ.get("SCANNER_OUTPUT", "dist/scanner-contribution.svg")
    write_svg(output_path, build_svg())
    print(f"Generated {Path(output_path).resolve()}")
