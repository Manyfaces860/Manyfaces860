from __future__ import annotations

import os
from pathlib import Path

from fetch_contributions import calendar_from_environment
from svg_common import (
    CELL_SIZE,
    LEVEL_COLORS,
    all_days,
    cell_center,
    cell_xy,
    geometry,
    labels,
    serpentine_days,
    svg_open,
    write_svg,
)

DURATION_SECONDS = 22
BODY_SEGMENTS = 11
SEGMENT_DELAY_SECONDS = 0.18


def motion_path(points: list[tuple[float, float]]) -> str:
    if not points:
        return "M 0 0"
    return " ".join(
        [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
        + [f"L {x:.1f} {y:.1f}" for x, y in points[1:]]
    )


def cell_animation(index: int, total: int) -> str:
    arrival = index / max(1, total - 1)
    after = min(1.0, arrival + 0.025)
    return (
        '<animate attributeName="fill" '
        f'values="#ff234b;#ff6781;#2a1118" '
        f'keyTimes="0;{arrival:.5f};{after:.5f}" '
        f'dur="{DURATION_SECONDS}s" repeatCount="indefinite" />'
    )


def build_svg() -> str:
    calendar = calendar_from_environment()
    geo = geometry(calendar)
    route = serpentine_days(calendar)
    path = motion_path([cell_center(day) for day in route])
    route_index = {(day.week_index, day.weekday): i for i, day in enumerate(route)}

    parts = [svg_open(calendar, "Centipede contribution trail")]
    parts.append(f'''  <defs>
    <filter id="redGlow" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="3.2" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="whiteGlow" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="2.2" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="100%" height="100%" rx="12" fill="#050505"/>
  <rect x="1" y="1" width="{geo.width - 2}" height="{geo.height - 2}" rx="12" fill="none" stroke="#292929"/>
''')
    parts.append(labels(calendar, "CENTIPEDE TRACE ACTIVE"))
    parts.append(f'  <path d="{path}" fill="none" stroke="#bd1838" stroke-width="1" opacity="0.14"/>\n')
    parts.append('  <g id="contribution-grid">\n')

    for day in all_days(calendar):
        x, y = cell_xy(day)
        fill = LEVEL_COLORS.get(day.level, LEVEL_COLORS["NONE"])
        title = f"{day.date}: {day.count} contributions"
        inner = ""
        if day.count > 0:
            inner = cell_animation(route_index[(day.week_index, day.weekday)], len(route))
        parts.append(
            f'    <rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="2" fill="{fill}">'
            f'<title>{title}</title>{inner}</rect>\n'
        )
    parts.append('  </g>\n')

    parts.append(f'''  <g filter="url(#whiteGlow)">
    <g>
      <animateMotion dur="{DURATION_SECONDS}s" repeatCount="indefinite" rotate="auto" path="{path}"/>
      <g stroke="#f4f4f4" stroke-width="1.2" stroke-linecap="round" opacity="0.9">
        <path d="M -8 -3 L -13 -7"/><path d="M -8 3 L -13 7"/>
        <path d="M 1 -5 L -1 -11"/><path d="M 1 5 L -1 11"/>
      </g>
      <ellipse cx="0" cy="0" rx="7.5" ry="5.7" fill="#f4f4f4" stroke="#8d8d8d" stroke-width="1"/>
      <circle cx="4.3" cy="-2" r="1.5" fill="#ff1744" filter="url(#redGlow)"/>
      <circle cx="4.3" cy="2" r="1.5" fill="#ff1744" filter="url(#redGlow)"/>
      <path d="M 7 -2 C 11 -4 12 -6 13 -8" fill="none" stroke="#f4f4f4" stroke-width="1"/>
      <path d="M 7 2 C 11 4 12 6 13 8" fill="none" stroke="#f4f4f4" stroke-width="1"/>
    </g>
''')

    for segment in range(1, BODY_SEGMENTS + 1):
        rx = max(3.3, 6.5 - segment * 0.20)
        ry = max(2.8, 5.0 - segment * 0.14)
        delay = -(segment * SEGMENT_DELAY_SECONDS)
        opacity = max(0.42, 1.0 - segment * 0.045)
        parts.append(
            f'    <ellipse rx="{rx:.2f}" ry="{ry:.2f}" fill="#efefef" stroke="#888888" '
            f'stroke-width="0.8" opacity="{opacity:.2f}">'
            f'<animateMotion dur="{DURATION_SECONDS}s" begin="{delay:.2f}s" '
            f'repeatCount="indefinite" rotate="auto" path="{path}"/></ellipse>\n'
        )

    parts.append('  </g>\n')
    parts.append(
        f'  <text x="{geo.width - 24}" y="{geo.height - 18}" text-anchor="end" '
        'fill="#555555" font-family="monospace" font-size="9">WHITE CENTIPEDE // CRIMSON RECORDS</text>\n'
    )
    parts.append('</svg>\n')
    return "".join(parts)


if __name__ == "__main__":
    output_path = os.environ.get("CENTIPEDE_OUTPUT", "dist/centipede-contribution.svg")
    write_svg(output_path, build_svg())
    print(f"Generated {Path(output_path).resolve()}")
